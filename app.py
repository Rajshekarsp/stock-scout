# app.py — Stock Scout (NSE indices auto-fetch)
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from io import StringIO
import datetime
import random

st.set_page_config(page_title="Stock Scout", layout="wide")

# --------------------------
# AUTH
# --------------------------
if "auth" not in st.session_state:
    st.session_state.auth = False

def login():
    st.title("🔐 Stock Scout Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "its_rajsp" and p == "G3nius@123":
            st.session_state.auth = True
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.auth:
    login()
    st.stop()

# --------------------------
# HELPERS: NSE lists
# --------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36",
    "Accept": "text/csv,application/json,text/plain,*/*",
}

INDEX_CSV_URLS = {
    "NIFTY 50": [
        "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        "https://www1.nseindia.com/content/indices/ind_nifty50list.csv",
    ],
    "NIFTY Midcap 100": [
        "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
        "https://www1.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    ],
    "NIFTY Smallcap 100": [
        "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
        "https://www1.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
    ],
}

# tiny hardcoded fallbacks if NSE is unreachable
FALLBACKS = {
    "NIFTY 50": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "ASIANPAINT", "BHARTIARTL"],
    "NIFTY Midcap 100": ["BHEL", "IRCTC", "UNIONBANK", "CROMPTON", "TVSMOTOR"],
    "NIFTY Smallcap 100": ["PNB", "RBLBANK", "UCOBANK", "NBCC", "CENTRALBK"],
}

@st.cache_data(ttl=3600)
def get_index_symbols(index_name: str) -> pd.DataFrame:
    urls = INDEX_CSV_URLS.get(index_name, [])
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.ok and len(r.text) > 100:
                df = pd.read_csv(StringIO(r.text))
                # Standardize column names (NSE CSV usually has 'Symbol' or 'Symbol ' etc.)
                cols = {c: c.strip() for c in df.columns}
                df.rename(columns=cols, inplace=True)
                if "Symbol" not in df.columns:
                    # Some files use 'SYMBOL'
                    if "SYMBOL" in df.columns:
                        df.rename(columns={"SYMBOL": "Symbol"}, inplace=True)
                return df[["Symbol"]].dropna().assign(Symbol=lambda s: s["Symbol"].str.strip().str.upper())
        except Exception:
            continue
    # fallback
    fb = FALLBACKS.get(index_name, [])
    return pd.DataFrame({"Symbol": fb})

def to_ns(ticker: str) -> str:
    t = ticker.strip().upper().replace(" ", "")
    return t if t.endswith(".NS") else f"{t}.NS"

# --------------------------
# UI CONTROLS
# --------------------------
st.title("📊 Stock Scout — NSE Scanner")

left, right = st.columns([3, 2], gap="large")
with left:
    universe = st.selectbox("Select Universe", ["NIFTY 50", "NIFTY Midcap 100", "NIFTY Smallcap 100", "Custom List"])
with right:
    # discrete horizon slider
    label_order = ["7D", "15D", "1M", "3M", "6M", "12M", "3Y", "5Y"]
    label_to_days = {"7D":7, "15D":15, "1M":30, "3M":90, "6M":180, "12M":365, "3Y":365*3, "5Y":365*5}
    horizon_label = st.select_slider("Timeframe", options=label_order, value="12M")

colA, colB, colC = st.columns([2,2,2])
with colA:
    invest_per_stock = st.number_input("Investment per stock (₹)", min_value=1000, max_value=5_00_00_000, value=100000, step=1000)
with colB:
    include_penny = st.checkbox("Filter to Penny (< ₹50)", value=False)
with colC:
    st.caption("Positive returns will be green; negative red. Confidence is simulated until the ML model is wired.")

# Determine tickers
if universe == "Custom List":
    custom = st.text_area("Enter comma-separated NSE tickers (e.g., RELIANCE, TCS, INFY):", "")
    base_symbols = [s.strip().upper() for s in custom.split(",") if s.strip()]
else:
    idx_df = get_index_symbols(universe)
    base_symbols = idx_df["Symbol"].tolist()

tickers_ns = [to_ns(s) for s in base_symbols]

# --------------------------
# DATA FETCH
# --------------------------
@st.cache_data(ttl=300, show_spinner=True)
def fetch_history(tickers: list, days_back: int) -> dict:
    """
    Returns dict[ticker] -> DataFrame with 'Close'
    Uses batch download; handles single-symbol edge cases.
    """
    if not tickers:
        return {}
    period = f"{max(days_back, 7)}d"  # at least 7d
    try:
        df = yf.download(tickers=" ".join(tickers), period=period, interval="1d", group_by="ticker", threads=True, auto_adjust=False, progress=False)
    except Exception:
        return {}

    out = {}
    if isinstance(df.columns, pd.MultiIndex):
        for t in tickers:
            try:
                sub = df[t]
                if "Close" in sub and not sub["Close"].dropna().empty:
                    out[t] = sub[["Close"]].dropna()
            except Exception:
                continue
    else:
        # single ticker case
        if "Close" in df and not df["Close"].dropna().empty:
            out[tickers[0]] = df[["Close"]].dropna()
    return out

days = label_to_days[horizon_label]
hist_map = fetch_history(tickers_ns, days)

# Current prices & returns
rows = []
for t in tickers_ns:
    close_series = hist_map.get(t)
    if close_series is None or close_series.empty:
        continue
    try:
        current = float(close_series["Close"].iloc[-1])
        start = float(close_series["Close"].iloc[0])
        ret_pct = ((current / start) - 1.0) * 100.0
        if include_penny and current >= 50:
            continue
        qty = invest_per_stock / current if current > 0 else np.nan
        proj_val = qty * current * (1 + ret_pct/100.0) if current > 0 else np.nan  # uses momentum as proxy
        conf = int(70 + (abs(hash(t)) % 26))  # 70–95 mock
        rows.append({
            "Stock": t.replace(".NS",""),
            "Ticker": t,
            "Current Price (₹)": round(current, 2),
            f"Return ({horizon_label}) %": round(ret_pct, 2),
            "Projected Value (₹)": round(proj_val, 2) if proj_val==proj_val else None,
            "Confidence (%)": conf
        })
    except Exception:
        continue

df = pd.DataFrame(rows)

# --------------------------
# RENDER
# --------------------------
st.markdown(f"**Universe:** {universe}  •  **Horizon:** {horizon_label}  •  **Investment/stock:** ₹{invest_per_stock:,}  •  **Rows:** {len(df)}")

if df.empty:
    st.warning("No data could be fetched (NSE list unavailable or Yahoo blocked). Try toggling filters or a different universe.")
else:
    # color positive/negative
    def color_ret(v):
        try:
            return "background-color: #2ecc71; color: black" if v >= 0 else "background-color: #c0392b; color: white"
        except Exception:
            return ""
    # sort by highest return by default
    sort_col = f"Return ({horizon_label}) %"
    df = df.sort_values(by=sort_col, ascending=False)
    st.dataframe(
        df.style.apply(lambda s: [color_ret(val) if s.name == sort_col else "" for val in s], axis=1),
        use_container_width=True,
        hide_index=True
    )

st.caption("Index constituents fetched from NSE CSV (with fallbacks). Prices via Yahoo Finance (.NS). Returns are simple momentum over the selected horizon; model predictions will replace this in the next iteration.")
