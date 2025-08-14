import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import joblib

# -----------------------------
# CONFIGURATION
# -----------------------------
USER_CREDENTIALS = {
    "its_rajsp": "password123"  # Change this before production
}

ML_MODEL_PATH = "stock_predictor.pkl"  # Placeholder for future ML model

# -----------------------------
# FUNCTIONS
# -----------------------------

def login():
    st.title("🔐 Stock Scout Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")


@st.cache_data
def fetch_stock_data(ticker, days):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    df = yf.download(ticker, start=start_date, end=end_date)
    if df.empty:
        return None

    df["SMA20"] = df["Close"].rolling(window=20).mean()

    latest_price = df["Close"].iloc[-1]
    sma20 = df["SMA20"].iloc[-1]

    return {
        "Company": yf.Ticker(ticker).info.get("longName", ticker),
        "Latest Price": round(latest_price),
        "SMA20": round(sma20) if not pd.isna(sma20) else None
    }


def get_suggestion_ml(ticker, latest_price):
    """Uses ML model if available, else returns None."""
    if os.path.exists(ML_MODEL_PATH):
        try:
            model = joblib.load(ML_MODEL_PATH)
            # Example: feature = [latest_price] — Replace with actual model features
            prediction = model.predict([[latest_price]])[0]
            return "Invest" if prediction == 1 else "Wait"
        except Exception as e:
            st.warning(f"ML model error: {e}")
            return None
    return None


def dashboard():
    st.title("📊 Stock Scout Dashboard")

    # Stock universe selection
    stock_universe = st.multiselect(
        "Select Stock Universe",
        ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS"],
        default=["TCS.NS", "INFY.NS"]
    )

    # Timeframe slider
    days = st.slider("Select timeframe (days)", min_value=30, max_value=365, value=90)

    # Investment per stock input
    investment_per_stock = st.number_input("Investment per stock (₹)", value=10000, step=1000)

    # Fetch & display
    data_rows = []
    for ticker in stock_universe:
        stock_data = fetch_stock_data(ticker, days)
        if stock_data:
            variance = round(investment_per_stock - stock_data["Latest Price"])

            # Try ML prediction
            ml_suggestion = get_suggestion_ml(ticker, stock_data["Latest Price"])

            # If no ML model, use SMA-based fallback logic
            if ml_suggestion is not None:
                suggestion = ml_suggestion
            else:
                suggestion = "Invest" if (stock_data["Latest Price"] < stock_data["SMA20"] and variance > 0) else "Wait"

            data_rows.append({
                "Company": stock_data["Company"],
                "Latest Price (₹)": stock_data["Latest Price"],
                "SMA20 (₹)": stock_data["SMA20"],
                "Variance (₹)": variance,
                "Suggestion": suggestion
            })

    df = pd.DataFrame(data_rows)

    # Display table
    st.dataframe(df, use_container_width=True)

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -----------------------------
# MAIN APP FLOW
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    dashboard()
