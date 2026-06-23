import requests
import json
import pandas as pd
import sqlalchemy as db
import os 
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
engine = db.create_engine('sqlite:///financials.db') # Initalizing the database
with engine.connect() as conn:
    conn.execute(db.text("""
        CREATE TABLE IF NOT EXISTS stock_data (
            ticker TEXT PRIMARY KEY,
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
    """))
    conn.commit()
def add_ticker(ticker,response): ## Add a new stock ticker to the database, maybe put api call in this function?
    data = response.json()['data']
    rows = {"ticker": ticker,
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
                ticker, current_price, market_cap, pe_ratio, revenue,
                revenue_growth, profit_margin, free_cash_flow, debt,
                analyst_rating, price_target
            ) VALUES (
                :ticker, :current_price, :market_cap, :pe_ratio, :revenue,
                :revenue_growth, :profit_margin, :free_cash_flow, :debt,
                :analyst_rating, :price_target
            )
        """), rows)
        conn.commit()
def display_stock_summary(ticker):
    with engine.connect() as conn:
        result = conn.execute(db.text("SELECT * FROM stock_data WHERE ticker = :ticker"), {"ticker": ticker}).mappings().fetchone()
        print(f"Stock Summary for {ticker}:")
        print(f"Current Price: {result['current_price']}")
        print(f"Market Cap: {result['market_cap']}")
        print(f"P/E Ratio: {result['pe_ratio']}")
        print(f"Revenue: {result['revenue']}")
        print(f"Revenue Growth: {result['revenue_growth']}")
        print(f"Profit Margin: {result['profit_margin']}")
        print(f"Free Cash Flow: {result['free_cash_flow']}")
        print(f"Total Debt: {result['debt']}")
        print(f"Analyst Rating: {result['analyst_rating']}")
        print(f"Price Target: {result['price_target']}")
        
"""
Let users choose inputs
""" 

ticker = str(input("Enter Ticker: "))
url = f"https://sugra.ai/api/v2/quotes/{ticker}/info"
params = {
    "fields": "currentPrice,marketCap,trailingPE,totalRevenue,revenueGrowth,profitMargins,freeCashflow,totalDebt,reccomdationKey,targetMeanPrice"
}
headers = {
    "x-api-key": os.getenv('SUGRA_API')
}
response = requests.get(
    url,
    params=params,
    headers=headers
)
add_ticker(ticker,response)
selected_stock = ticker 


options = print(" [1] Stock Summary\n",
                "[2] Latest News\n",
                "[3] Recent Move\n", 
                "[4] Risks")
action = int(input("Choose action: ")) 
if action == 1:
    display_stock_summary(selected_stock)


# Get data    
type_data = {1: '/annual/income-statement', 
            2: 'news', 
            3: '', 
            4: ''}

## gemini to be used later
# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     config=types.GenerateContentConfig(
#       system_instruction="You are a university instructor and can explain programming concepts clearly in a few words."
#     ),
#     contents="What are the advantages of pair programming?",
# )

# print(response.text)

