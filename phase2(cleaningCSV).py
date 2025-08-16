import pandas as pd
import yfinance as yf
from datetime import timedelta
import time

# Step 1: Load and clean numeric columns
def clean_numeric_columns(df):
    df = df.replace(['NA', 'na', '-', 'NaN', 'nan'], '0')
    df = df.apply(lambda col: col.map(lambda x: str(x).replace(',', '').replace('%', '') if isinstance(x, str) else x))
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.fillna(0)
    return df

# Load the flat-format Excel
df = pd.read_excel("labeled_data.xlsx")
df.columns = df.columns.str.strip()

# Clean numeric columns (excluding Stock)
numeric_df = clean_numeric_columns(df.drop(columns=["Stock"]))
df = pd.concat([df["Stock"], numeric_df], axis=1)

# Save cleaned version
df.to_excel("flattened_stocks.xlsx", index=False)
print("✅ Cleaned data saved to 'flattened_stocks.xlsx'")

# --- Step 2: Labeling using YFinance ---

def label_stock(r1, r2, r3, r4):
    avg_return = (r1 + r2 + r3 + r4) / 4
    if avg_return <= 0.05:
        return 'Sell'
    elif avg_return >= 0.20:
        return 'Average'        
    else:
        return 'Hold'  

def fetch_price(symbol, date):
    try:
        df = yf.download(
            f"{symbol}.NS",
            start=date,
            end=(pd.to_datetime(date) + timedelta(days=5)).strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True
        )
        if df.empty or 'Close' not in df.columns or df['Close'].dropna().empty:
            return None
        value = df['Close'].dropna().iloc[0]
        return float(value)


    except Exception as e:
        print(f"⚠️ Error fetching price for {symbol} on {date}: {e}")
        return None

# Define price dates
price_dates = {
    "Mar 2024": "2024-03-31",
    "Jun 2024": "2024-06-30",
    "Sep 2024": "2024-09-30",
    "Dec 2024": "2024-12-31",
    "Mar 2025": "2025-03-31"
}

ratings = []
for idx, row in df.iterrows():
    stock_name = row["Stock"]
    try:
        prices = {}
        for q, d in price_dates.items():
            p = fetch_price(stock_name, d)
            time.sleep(1)  # prevent rate limiting
            if p is None:
                raise Exception(f"Missing price for {q}")
            prices[q] = p

        r1 = (prices["Jun 2024"] - prices["Mar 2024"]) / prices["Mar 2024"]
        r2 = (prices["Sep 2024"] - prices["Jun 2024"]) / prices["Jun 2024"]
        r3 = (prices["Dec 2024"] - prices["Sep 2024"]) / prices["Sep 2024"]
        r4 = (prices["Mar 2025"] - prices["Dec 2024"]) / prices["Dec 2024"]

        label = label_stock(r1, r2, r3, r4)
        ratings.append(label)
    except Exception as e:
        print(f"⚠️ Skipping {stock_name}: {e}")
        ratings.append("Data Error")

df["Rating"] = ratings
df.to_excel("labeled_stocks_with_price.xlsx", index=False)
print("✅ Labeled data saved to 'labeled_stocks_with_price.xlsx'")
