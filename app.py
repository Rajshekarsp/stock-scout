import streamlit as st
import pandas as pd
import yfinance as yf
import joblib
from datetime import datetime, timedelta

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="Stock Scout", layout="wide")

# -----------------------
# SESSION STATE
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# -----------------------
# LOGIN
# -----------------------
def login():
    st.title("🔐 Login to Stock Scout")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "its_rajsp" and password == "1234":  # change password later!
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")

# -----------------------
# STOCK UNIVERSE SELECTION
# -----------------------
def stock_app():
    st.title(f"📊 Stock Scout - Welcome {st.session_state.username}")

    # Stock universe input
    default_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
    tickers = st.text_area("Enter Stock Symbols (comma separated)", ",".join(default_stocks))
    tickers = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    # Time frame slider
    days = st.slider("Select Time Frame (in days from today)", min_value=1, max_value=365, value=30)

    # Fetch prices
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    data = yf.download(tickers, start=start_date, end=end_date)["Close"]

    # Convert to latest price
    latest_prices = data.iloc[-1]

    # Investment per stock (for variance calculation)
    investment_per_stock = st.number_input("Investment per Stock (INR)", min_value=1, value=1000)

    # Create DataFrame with company names
    rows = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            company_name = info.get("longName", ticker)
            price = latest_prices.get(ticker, 0)
            variance = round(price - investment_per_stock, 0)
            suggestion = "Invest" if variance < 0 else "Wait"
            rows.append([company_name, int(price), variance, suggestion])
        except Exception:
            rows.append([ticker, 0, 0, "Wait"])

    df = pd.DataFrame(rows, columns=["Company", "Price (INR)", "Variance (INR)", "Suggestion"])

    # Display table without decimals
    st.dataframe(df, hide_index=True)

    # Download CSV
    csv = df.to_csv(index=False)
    st.download_button("📥 Download CSV", data=csv, file_name="stock_data.csv", mime="text/csv")

    # Placeholder for ML Model
    st.info("📌 ML model integration coming soon.")

# -----------------------
# MAIN FLOW
# -----------------------
if not st.session_state.logged_in:
    login()
else:
    stock_app()
