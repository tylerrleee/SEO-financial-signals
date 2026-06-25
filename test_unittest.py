import os
os.environ['SUGRA_API'] = 'placeholder'  

import pytest
import sqlalchemy as db
from unittest.mock import MagicMock, patch
import utils

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS stock_data (
        ticker TEXT PRIMARY KEY,
        last_updated DATETIME,
        current_price REAL,
        market_cap INTEGER,
        pe_ratio REAL,
        revenue INTEGER,
        revenue_growth REAL,
        profit_margin REAL,
        free_cash_flow INTEGER,
        debt INTEGER,
        analyst_rating TEXT,
        price_target REAL
    )
"""

@pytest.fixture
def fake_engine():
    engine = db.create_engine('sqlite:///:memory:')
    with engine.connect() as conn:
        conn.execute(db.text(CREATE_TABLE))
        conn.commit()
    return engine


def test_add_ticker(fake_engine):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': {
            'currentPrice': 100.0,
            'marketCap': 100,
            'trailingPE': 10.0,
            'totalRevenue': 100,
            'revenueGrowth': 0.10,
            'profitMargins': 0.10,
            'freeCashflow': 100,
            'totalDebt': 100,
            'reccomdationKey': 'buy',
            'targetMeanPrice': 100.0,
        }
    }

    with patch.object(utils, 'engine', fake_engine):
        utils.add_ticker('AAPL', mock_response)

    with fake_engine.connect() as conn:
        row = conn.execute(
            db.text("SELECT * FROM stock_data WHERE ticker = 'AAPL'")
        ).mappings().fetchone()

    assert row is not None
    assert row['ticker'] == 'AAPL'
    assert row['current_price'] == 100.0
    assert row['analyst_rating'] == 'buy'


def test_get_available_tickers(fake_engine):
    with fake_engine.connect() as conn:
        conn.execute(db.text("""
            INSERT INTO stock_data (ticker, last_updated, current_price)
            VALUES ('AAPL', '2024-01-01', 100.0), ('MSFT', '2024-01-01', 100.0)
        """))
        conn.commit()

    with patch.object(utils, 'engine', fake_engine):
        tickers = utils.get_available_tickers()

    assert 'AAPL' in tickers
    assert 'MSFT' in tickers
    assert len(tickers) == 2


def test_display_stock_summary(fake_engine, capsys):
    with fake_engine.connect() as conn:
        conn.execute(db.text("""
            INSERT INTO stock_data (
                ticker, last_updated, current_price, market_cap, pe_ratio, revenue,
                revenue_growth, profit_margin, free_cash_flow, debt, analyst_rating, price_target
            ) VALUES (
                'AAPL', '2024-01-01', 250.0, 1, 1.0, 1,
                1.0, 1.0, 1.0, 1.0, 'buy', 1.0
            )
        """))
        conn.commit()

    with patch.object(utils, 'engine', fake_engine):
        utils.display_stock_summary('TSLA')

    stock_output = capsys.readouterr().out ##from terminal
    assert 'TSLA' in stock_output
    assert '250.00$' in stock_output
    assert 'buy' in stock_output
