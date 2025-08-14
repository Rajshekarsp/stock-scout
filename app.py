import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Stock Scout", layout="wide")

# ---------------- SAFE FETCH FUNCTION ----------------
@st.cache_data
def fetch_prices(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m")

        # If no data returned
        if df.empty or 'Close' not in df.columns:
            return None

        # Get last close price
        last_close = df['Close'].iloc[-1]

        # Handle NaN in last close
        if pd.isna(last_close):
            valid_rows = df['Close'].dropna()
            if valid_rows.empty:
                return None
            last_close = valid_rows.iloc[-1]

        return float(last_close)

    except Exception:
        return None

# ---------------- INDIAN NSE STOCK LIST ----------------
stock_symbols = [
    "RELIANCE.NS",  # Reliance Industries
    "TCS.NS",       # Tata Consultancy Services
    "INFY.NS",      # Infosys
    "HDFCBANK.NS",  # HDFC Bank
    "ICICIBANK.NS", # ICICI Bank
    "SBIN.NS",      # State Bank of India
    "BHARTIARTL.NS",# Bharti Airtel
    "ITC.NS",       # ITC Limited
    "LT.NS",        # Larsen & Toubro
    "ASIANPAINT.NS" # Asian Paints
]

# ---------------- UI ----------------
st.title("📊 Stock Scout - NSE Live Prices")
st.subheader("Live NSE stock prices (updates on refresh)")

# Fetch prices
data = []
for symbol in stock_symbols:
    price = fetch_prices(symbol)
    if price is None:
        data.append({"Symbol": symbol.replace(".NS", ""), "Price (₹)": "-"})
    else:
        data.append({"Symbol": symbol.replace(".NS", ""), "Price (₹)": f"{price:.2f}"})

# Display table
df_prices = pd.DataFrame(data)
st.dataframe(df_prices, use_container_width=True)

st.caption("Data provided by Yahoo Finance | Prices update on page refresh")
