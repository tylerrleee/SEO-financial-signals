import requests
import json, os
import pandas as pd
import sqlalchemy as db
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# TODO Mock API response
# Mock DB
# Mock SQL queries
api_key = os.getenv('SUGRA_API')
if not api_key:
    raise ValueError("SUGRA_API environment variable is not set.")
engine = db.create_engine('sqlite:///financials.db') # Initalizing the database

params = {
    "fields": "currentPrice,marketCap,trailingPE,totalRevenue,revenueGrowth,profitMargins,freeCashflow,totalDebt,reccomdationKey,targetMeanPrice"
}
headers = {"x-api-key": api_key}
def get_engine():
    return engine

def ticker_input():
    while True:
        ticker = input("Enter Ticker: ").strip().upper()
        if not ticker:
            continue
            
        url = f"https://sugra.ai/api/v2/quotes/{ticker}/info"
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            # This will raise an exception for 4xx/5xx status codes
            response.raise_for_status() 
            
            
            # Logic for your database
            if ticker not in get_available_tickers():
                add_ticker(ticker, response)
            
            return ticker
            
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An unexpected error occurred: {err}")
        
        print("Please try again :D")


def add_ticker(ticker,response): ## Add a new stock ticker to the database, maybe put api call in this function?
    
    data = response.json()['data']
    
    
    rows = {"ticker": ticker,
            "last_updated": datetime.now(),
            "current_price": data.get("currentPrice"),
            "market_cap": data.get("marketCap"),
            "pe_ratio": data.get("trailingPE"),
            "revenue": data.get("totalRevenue"),
            "revenue_growth": data.get("revenueGrowth"),
            "profit_margin": data.get("profitMargins"),
            "free_cash_flow": data.get("freeCashflow"),
            "debt": data.get("totalDebt"),
            "analyst_rating": data.get("reccomdationKey"),
            "price_target": data.get("targetMeanPrice")
            }
    with engine.connect() as conn:
        conn.execute(db.text("""
            INSERT OR REPLACE INTO stock_data (
                ticker, last_updated, current_price, market_cap, pe_ratio, revenue,
                revenue_growth, profit_margin, free_cash_flow, debt,
                analyst_rating, price_target
            ) VALUES (
                :ticker, :last_updated, :current_price, :market_cap, :pe_ratio, :revenue,
                :revenue_growth, :profit_margin, :free_cash_flow, :debt,
                :analyst_rating, :price_target
            )
        """), rows)
        conn.commit()
    

def get_available_tickers():
    try:
        with engine.connect() as conn:
            unique_tickers = conn.execute(db.text("""
                                SELECT DISTINCT ticker
                                FROM stock_data
                                """
                                )).scalars().all()
        return unique_tickers
    except Exception as e:
        print(f"Database does not exist, or no tickers available: {e}")
        return []
    
def display_stock_summary(ticker):
    try:
        with engine.connect() as conn:
            result = conn.execute(db.text("SELECT * FROM stock_data WHERE ticker = :ticker"), {"ticker": ticker}).mappings().fetchone()
            print("\n ===" * 10)
            print(f"Stock Summary for {ticker}:")
            print("===" * 10)
            print(f"Current Price: {result['current_price']:,.2f}$")
            print(f"Market Cap: {result['market_cap']:,.2f}$")
            print(f"P/E Ratio: {result['pe_ratio']}")
            print(f"Revenue: {result['revenue']:,.2f}$")
            print(f"Revenue Growth: {result['revenue_growth']}")
            print(f"Profit Margin: {result['profit_margin']}")
            print(f"Free Cash Flow: {result['free_cash_flow']:,.2f}$")
            print(f"Total Debt: {result['debt']:,.2f}$")
            print(f"Analyst Rating: {result['analyst_rating']}")
            print(f"Price Target: {result['price_target']:,.2f}$")
            print("===" * 6)
        
    
    except Exception as e:
        print(f"Ticker does not exist: {e}")
    
