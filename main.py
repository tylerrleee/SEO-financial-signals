import requests
import json
import pandas as pd
import sqlalchemy as db
import os 
from google import genai
from google.genai import types

"""
Let users choose inputs
"""

ticker = str(input("Enter Ticker: "))
options = print(" [1] Stock Summary\n",
                "[2] Latest News\n",
                "[3] Recent Move\n", 
                "[4] Risks")
action = int(input("Choose action: "))  

# Get data    
type_data = {1: '/annual/income-statement', 
            2: 'news', 
            3: '', 
            4: ''}

url = f"https://sugra.ai/api/v2/quotes/{ticker}/{}"
params = {
    "fields": "website,industry"
}
headers = {
    "x-api-key": os.getenv('SUGRA_API')
}
response = requests.get(
    url,
    params=params,
    headers=headers
)

# Get db
stock_data = response.json()['data']
df = pd.DataFrame.from_dict([stock_data])
engine = db.create_engine('sqlite:///financials.db')
df.to_sql('stock_data', con=engine, if_exists='replace', index=False)

with engine.connect() as connection:
   query_result = connection.execute(db.text("SELECT * FROM stock_data;")).fetchall()
   print(pd.DataFrame(query_result))


# ai
client = genai.Client(
    api_key=os.geenv('GEMINI_API')
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
      system_instruction="You are a university instructor and can explain programming concepts clearly in a few words."
    ),
    contents="What are the advantages of pair programming?",
)

print(response.text)

