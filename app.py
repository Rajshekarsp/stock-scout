import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Stock Scout", layout="wide")

# Title
st.title("📊 Stock Scout")

# Stock universe selection
universe = st.selectbox(
    "Select Stock Universe",
    ["NSE Large Cap", "NSE Mid Cap", "NSE Penny Stocks"]
)

# Sample stock lists
stock_lists = {
    "NSE Large Cap": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
    "NSE Mid Cap": ["ADANIGREEN.NS", "IRCTC.NS", "NAM-INDIA.NS"],
    "NSE Penny Stocks": ["SUZLON.NS", "YESBANK.NS", "IDEA.NS"]
}

selected_stocks = stock_lists.get(universe, [])

if not selected_stocks:
    st.error("No stocks found for the selected universe.")
else:
    try:
        data = []
        for ticker in selected_stocks:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")

            # Skip if no data
            if hist.empty:
                continue

            current_price = hist["Close"].iloc[-1]

            week_return = None
            if len(hist) >= 5:
                week_return = ((hist["Close"].iloc[-1] / hist["Close"].iloc[-5]) - 1) * 100

            year_return = None
            if len(hist) > 0:
                year_return = ((hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1) * 100

            data.append({
                "Stock": ticker,
                "Current Price (INR)": round(current_price, 2),
                "7 Day Return (%)": round(week_return, 2) if week_return is not None else None,
                "12 Month Return (%)": round(year_return, 2) if year_return is not None else None
            })

        if not data:
            st.warning("No price data could be fetched for the selected stocks.")
        else:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
