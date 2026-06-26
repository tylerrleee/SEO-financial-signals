import requests
import json
import pandas as pd
import sqlalchemy as db
import os 
from utils import *
from colorama import Fore, Style
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
params = {
    "fields": "currentPrice,marketCap,trailingPE,totalRevenue,revenueGrowth,profitMargins,freeCashflow,totalDebt,reccomdationKey,targetMeanPrice"
}
headers = {
    "x-api-key": os.getenv('SUGRA_API')
}
engine = get_engine() # Initalizing the database



with engine.connect() as conn:
    conn.execute(db.text("""
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
    """))
    conn.commit()

"""
Let users choose inputs
"""

ticker = ticker_input()
news_url = f"https://sugra.ai/api/v2/quotes/{ticker}/news"

selected_stock = ticker 
main_loop = True

while main_loop:
    try: 
        print(f"Selected Stock: {selected_stock}\n")
        options = print(" [1] Stock Summary\n",
                        "[2] Latest News\n",
                        "[3] Switch Ticker\n",
                        "[4] Add/Update Ticker \n",
                        "[5] Generate AI Summary\n",
                        "[6] Show all Stocks in Database\n",
                        "[7] Exit\n")
        action = int(input("Choose action: ")) 
        if action == 1:
            print("\n" * 10)
            display_stock_summary(selected_stock)
            print("\n" * 10)
        elif action == 2:
            print("\n" * 10)

            news_response = requests.get(
                news_url,
                headers=headers
            )
            news_data = news_response.json()['data']
            print(f"Latest News for {selected_stock}:")
            for article in news_data:
                print("-----------------------------")
                print(f"Title: {article['title']}")
                print(f"Date: {article['pubDate']}")
                print(f"Source: {article['source']}")
                print(f"URL: {article['link']}\n")
            input("Press Enter to continue...")
            print("\n" * 10)

        elif action == 3:
            print("\n" * 10)
            new_ticker = ticker_input()
            selected_stock = new_ticker
            news_url = f"https://sugra.ai/api/v2/quotes/{selected_stock}/news"
            print("\n" * 10)

        elif action == 4:
            
            new_ticker = str(input("Enter Ticker to add/update: "))
            url = f"https://sugra.ai/api/v2/quotes/{new_ticker}/info"
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
            add_ticker(new_ticker,response)
            selected_stock = new_ticker
            news_url = f"https://sugra.ai/api/v2/quotes/{selected_stock}/news"
            print("\n" * 10)
        elif action == 5:
            
            # Get stock data
            with engine.connect() as conn:
                financial_record = conn.execute(
                    db.text("SELECT * FROM stock_data WHERE ticker = :ticker"), 
                    {"ticker": selected_stock}
                ).mappings().fetchone()

            # Get lates tnews article 
            news_response = requests.get(news_url, headers=headers)
            news_data = news_response.json().get('data', [])
            
            print(f"\nAnalyzing data and generating strategic timeline for {selected_stock}...")

            # Formatting to inject prompt 

            news_summary = ""
            for article in news_data[:5]:           # limit to 5 latest articles 
                news_summary += f"- Title: {article['title']} (Source: {article['source']})\n"

            prompt = f"""
            Analyze this company's financial state and news context to construct a competitive strategic map.
            
            FINANCIAL DATA:
            {financial_record}
            
            RECENT NEWS HEADLINES:
            {news_summary}
            

            INSTRUCTIONS:
            Output a clear text-based visual map using the following exact structure:
            
            [ CENTRAL COMPANY: {selected_stock} ]
            |
            +-- [ STRATEGIC THEME A: (Name of theme, e.g., AI Expansion) ]
            |    |-- Quarter Milestone: (What milestone are they hit or hitting?)
            |    |-- Signal: (Based on news or capital movement/revenue growth)
            |    +-- Confidence Level: (Low/Medium/High % based on coverage & earnings strength)
            |
            +-- [ STRATEGIC THEME B: (Name of theme, e.g., Cost Reduction) ]
                    |-- Quarter Milestone: ...
                    |-- Signal: ...
                    +-- Confidence Level: ...
            
            Keep it concise, realistic, and highly scannable for a terminal screen. If mentioning a financial keyword or acronym (DCF, FCF, discounted cashflow), 
            briefly explain what it means at the bottom.
            For example, "P/E ratio is the Price-to-Earnings ratio. How much investors pay per $1 of profit." 

            Formatting:
            - Use pipes ('|'), intersections ('+') and '/ \ > < -' to show a tree structure that shows connections.
            Edge Cases:
            1. In the case that the ticker is invalid or does not exist in any stock exchanges, prompt user 
                to reenter stock tickers that exists in a public exchange. 
            2. In the case that the company just IPO'd, include information that is provided and its IPO filings, 
                do not use information on your own accord. 
            
            3. If it is an index fund,
            """
            # Call Gemini API
            try:
                client   = genai.Client(api_key = os.getenv('GEMINI_API'))
                response = client.models.generate_content(
                    model = "gemini-3.1-flash-lite"
                    , contents = prompt
                )
                # ANSI color codes
                CYAN = '\033[96m'
                GREEN = '\033[92m'
                YELLOW = '\033[93m'
                RESET = '\033[0m'
                BOLD = '\033[1m'

                print("\n ", CYAN + "====" * 10, "OUTPUT", "====" * 10 + RESET)
                colored_output = response.text
                
                # Highlight key sections
                colored_output = colored_output.replace("[ CENTRAL COMPANY:", f"{BOLD}{CYAN}[ CENTRAL COMPANY:{RESET}")
                colored_output = colored_output.replace("[ STRATEGIC THEME", f"{BOLD}{GREEN}[ STRATEGIC THEME{RESET}")
                colored_output = colored_output.replace("Confidence Level:", f"{YELLOW}Confidence Level:{RESET}")
                print(colored_output)
                print(CYAN + "====" * 21 + RESET)
            except Exception as e:
                print(f"Error calling Gemini API: {e}")
            input("Press Enter to continue...")
        elif action == 6:
            with engine.connect() as conn:
                result = conn.execute(db.text("SELECT ticker, current_price FROM stock_data")).mappings().fetchall()
                print("\n" * 10)
                print("Compact View of All Stocks:\n")
                print("---"*10)
                for row in result:
                    price = f"{row['current_price']:,.2f}$" if row['current_price'] is not None else "N/A"
                    print(f"{Fore.RED}Ticker: {Style.RESET_ALL}{row['ticker']}, {Fore.BLUE}Current Price: {Style.RESET_ALL}{price}")
                input("\nPress Enter to continue...")
                
        elif action == 7:
            print("\nBye!!!\n")
            main_loop = False

    except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
    except Exception as err:
            print(f"An unexpected error occurred: {err}")
        



# print(response.text)

# TODO: output formatting (colors, ..)
# TODO: edge cases 
# 1. ticker don't exist
# 2. company IPO (None data exists)
# TODO: 3 or more unit tests