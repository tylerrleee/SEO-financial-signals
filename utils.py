import requests
import json, os
import pandas as pd
import sqlalchemy as db
from datetime import datetime
from dotenv import load_dotenv
import sys
import tty
import termios
from colorama import Fore, Style, init

init(autoreset=True)
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

def get_single_key():
    """
    Reads single character from keyboard without pressing enter

    """

    # get file descriptor & jump to bottom
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    # read one character from standard input
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

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
    
def format_value(value, format_spec=""):
    return format(value, format_spec) if value is not None else "N/A"

def display_stock_summary(ticker):

    # Variable Red : definition italic
    definitions = {
        f"{Fore.RED}Current Price{Style.RESET_ALL}" : f"{Style.DIM}The price of one share right now.{Style.RESET_ALL}",
        f"{Fore.RED}Market Cap{Style.RESET_ALL}"    : f"{Style.DIM}Total value of all shares combined.{Style.RESET_ALL}",
        f"{Fore.RED}P/E Ratio{Style.RESET_ALL}"     : f"{Style.DIM}Price-to-Earnings ratio. How much investors pay per $1 of profit.{Style.RESET_ALL}",
        f"{Fore.RED}Revenue{Style.RESET_ALL}"       : f"{Style.DIM}Total money the company brought in from sales before any expenses.{Style.RESET_ALL}",
        f"{Fore.RED}Revenue Growth{Style.RESET_ALL}": f"{Style.DIM}How much revenue increased compared to the same period last year.{Style.RESET_ALL}",
        f"{Fore.RED}Profit Margin{Style.RESET_ALL}" : f"{Style.DIM}Percentage of revenue that becomes actual profit after expenses.{Style.RESET_ALL}",
        f"{Fore.RED}Free Cash Flow{Style.RESET_ALL}": f"{Style.DIM}Cash left over after expenses, which can be used for growth or paying debt.{Style.RESET_ALL}",
        f"{Fore.RED}Total Debt{Style.RESET_ALL}"    : f"{Style.DIM}All the money the company owes, higher = more risk.{Style.RESET_ALL}",
        f"{Fore.RED}Analyst Rating{Style.RESET_ALL}": f"{Style.DIM}Wall Street's opinion, either buy, hold, or sell.{Style.RESET_ALL}",
        f"{Fore.RED}Price Target{Style.RESET_ALL}"  : f"{Style.DIM}The average price analysts predict the stock will reach within the next 12 months.{Style.RESET_ALL}",
    }

    try:
        with engine.connect() as conn:
            result = conn.execute(db.text("SELECT * FROM stock_data WHERE ticker = :ticker"), {"ticker": ticker}).mappings().fetchone()

            show_definitions = False
            while True:
                print("\n" * 10)
                print(f"Stock Summary for {ticker}:")
                print("===" * 10)

                metrics = [
                    ("Current Price",   format_value(result['current_price'], ',.2f') + "$" if result['current_price'] is not None else "N/A"),
                    ("Market Cap",      format_value(result['market_cap'], ',.2f') + "$" if result['market_cap'] is not None else "N/A"),
                    ("P/E Ratio",       format_value(result['pe_ratio'], '.2f')),
                    ("Revenue",         format_value(result['revenue'], ',.2f') + "$" if result['revenue'] is not None else "N/A"),
                    ("Revenue Growth",  format_value(result['revenue_growth'])),
                    ("Profit Margin",   format_value(result['profit_margin'], '.2%')),
                    ("Free Cash Flow",  format_value(result['free_cash_flow'], ',.2f') + "$" if result['free_cash_flow'] is not None else "N/A"),
                    ("Total Debt",      format_value(result['debt'], ',.2f') + "$" if result['debt'] is not None else "N/A"),
                    ("Analyst Rating",  format_value(result['analyst_rating'])),
                    ("Price Target",    format_value(result['price_target'], ',.2f') + "$" if result['price_target'] is not None else "N/A"),
                ]

                for metric_name, metric_value in metrics:
                    formatted_key = f"{Fore.RED}{metric_name}{Style.RESET_ALL}"
                    print(f"{formatted_key}: {metric_value}", end="")
                    if show_definitions:
                        def_key = f"{Fore.RED}{metric_name}{Style.RESET_ALL}"
                        print(f" | {definitions[def_key]}")
                    else:
                        print()

                print("===" * 6)
                print("Press 'x' to toggle definitions, or any other key to exit")

                key = get_single_key()
                if key.lower() == 'x':
                    show_definitions = not show_definitions
                else:
                    break

    except Exception as e:
        print(f"Ticker does not exist: {e}")
    
