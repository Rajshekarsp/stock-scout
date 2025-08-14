import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ------------------------------
# Helper function to get company name
# ------------------------------
def get_company_name(ticker):
    try:
        return yf.Ticker(ticker).info.get("longName", ticker)
    except:
        return ticker

# ------------------------------
# Fetch price data
# ------------------------------
@st.cache_data
def fetch_prices(tickers, days):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    data = {}
    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date)
        if not df.empty:
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            data[ticker] = df
    return data

# ------------------------------
# Suggestion logic
# ------------------------------
def get_suggestion(latest_price, sma20, invest_price):
    if pd.isna(sma20):  # Not enough data for SMA
        return "Wait"
    variance_pct = ((latest_price - invest_price) / invest_price) * 100
    if latest_price > sma20 and abs(variance_pct) <= 5:
        return "Invest"
    return "Wait"

# ------------------------------
# Color formatting for Suggestion
# ------------------------------
def color_suggestion(suggestion):
    if suggestion == "Invest":
        return f"<span style='color:green; font-weight:bold'>{suggestion}</span>"
    else:
        return f"<span style='color:red; font-weight:bold'>{suggestion}</span>"

# ------------------------------
# Streamlit App Layout
# ------------------------------
st.set_page_config(page_title="Stock Scout", layout="wide")

st.title("📈 Stock Scout")

# Login simulation (placeholder)
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if username and password:  # No real auth yet
    st.success(f"Welcome {username}!")

    # Choose stocks
    tickers_input = st.text_area("Enter stock tickers (comma separated)", "TCS.NS, RELIANCE.NS, INFY.NS")
    tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]

    # Timeframe
    days = st.slider("Select timeframe (days from today)", min_value=30, max_value=365, value=180)

    # Investment per stock
    invest_per_stock = st.number_input("Investment price per stock (INR)", value=3500)

    if st.button("Fetch Data"):
        prices_data = fetch_prices(tickers, days)

        results = []
        for ticker, df in prices_data.items():
            latest_price = df['Close'].iloc[-1]
            sma20 = df['SMA20'].iloc[-1]
            company_name = get_company_name(ticker)
            variance_inr = latest_price - invest_per_stock
            suggestion = get_suggestion(latest_price, sma20, invest_per_stock)

            results.append({
                "Company": company_name,
                "Current Price (₹)": int(latest_price),
                "SMA20 (₹)": int(sma20) if not pd.isna(sma20) else None,
                "Variance (₹)": int(variance_inr),
                "Suggestion": color_suggestion(suggestion)
            })

        df_results = pd.DataFrame(results)
        # Render with HTML to keep colors
        st.markdown(df_results.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("Please log in to view stock data.")

# ------------------------------
# Placeholder for ML model
# ------------------------------
# In the future, replace `get_suggestion()` with ML model predictions here.
