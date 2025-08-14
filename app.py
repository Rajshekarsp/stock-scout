import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="Stock Scout", layout="wide")

# ----------------------------
# Helper Functions
# ----------------------------
def fetch_data(ticker, period_days):
    end = datetime.today()
    start = end - timedelta(days=period_days)
    data = yf.download(ticker, start=start, end=end)
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    return data

def get_company_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get('longName', ticker)
    except:
        return ticker

def get_suggestion(latest_price, sma20, invest_per_stock):
    # Ensure scalar values
    if not isinstance(latest_price, (int, float)):
        latest_price = float(latest_price.iloc[-1]) if hasattr(latest_price, "iloc") else float(latest_price)

    if not isinstance(sma20, (int, float)):
        sma20 = float(sma20.iloc[-1]) if hasattr(sma20, "iloc") else float(sma20)

    variance_inr = invest_per_stock - latest_price

    # Suggestion logic
    if latest_price > sma20 and abs(variance_inr) <= 0.05 * invest_per_stock:
        return "Wait"
    else:
        return "Invest"

# ----------------------------
# UI
# ----------------------------
st.title("📊 Stock Scout")

# Slider for time frame
period_map = {
    "7 Days": 7,
    "15 Days": 15,
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "12 Months": 365,
    "3 Years": 1095,
    "5 Years": 1825
}

timeframe = st.select_slider(
    "Select Time Frame:",
    options=list(period_map.keys()),
    value="1 Month"
)

# Investment amount per stock
invest_per_stock = st.number_input("Investment per Stock (INR)", value=1000, step=100)

# Universe of stocks (Example)
tickers = ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS"]

# Fetch & Display Data
rows = []
for ticker in tickers:
    df = fetch_data(ticker, period_map[timeframe])
    if df.empty:
        continue

    company_name = get_company_name(ticker)
    latest_price = df['Close'].iloc[-1]
    sma20 = df['SMA20'].iloc[-1]
    variance_inr = int(round(invest_per_stock - latest_price, 0))
    suggestion = get_suggestion(latest_price, sma20, invest_per_stock)

    rows.append({
        "Company": company_name,
        "Latest Price (INR)": int(round(latest_price, 0)),
        "SMA20 (INR)": int(round(sma20, 0)) if pd.notna(sma20) else None,
        "Variance (INR)": variance_inr,
        "Suggestion": suggestion
    })

df_display = pd.DataFrame(rows)

# Remove decimals
df_display = df_display.applymap(lambda x: int(x) if isinstance(x, float) else x)

st.dataframe(df_display, use_container_width=True)
