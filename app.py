import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit page config
st.set_page_config(page_title="Stock Scout - NSE Live Prices", layout="wide")

# Title and description
st.title("📊 Stock Scout - NSE Live Prices")
st.markdown("### Live NSE stock prices (updates on refresh)")

# NSE stock symbols with .NS suffix
symbols = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
    "LT.NS", "ASIANPAINT.NS"
]

# Fetch stock prices
def get_live_prices(symbol_list):
    data = []
    for symbol in symbol_list:
        try:
            stock = yf.Ticker(symbol)
            price = stock.history(period="1d")["Close"].iloc[-1]
            data.append({"Symbol": symbol.replace(".NS", ""), "Price (₹)": round(price, 2)})
        except Exception as e:
            data.append({"Symbol": symbol.replace(".NS", ""), "Price (₹)": "-"})
    return pd.DataFrame(data)

# Fetch and display prices
df = get_live_prices(symbols)
st.table(df)

st.caption("Data provided by Yahoo Finance | Prices update on page refresh")
