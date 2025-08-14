
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(page_title="Stock Scout (Mock)", layout="wide")

USERNAME = "its_rajsp"
PASSWORD = "G3nius@123"

# --- Session State ---
if "auth" not in st.session_state:
    st.session_state.auth = False

# --- Login ---
def login_form():
    with st.form("login"):
        st.title("🔐 Stock Scout Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Login")
        if ok:
            if u == USERNAME and p == PASSWORD:
                st.session_state.auth = True
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

if not st.session_state.auth:
    login_form()
    st.stop()

# --- Header ---
st.title("📊 Stock Scout (Mock — Functional Table)")
st.caption("Universe: NIFTY 100 / Penny / Both • Period slider controls prediction horizon • Table is sortable & filterable")

# --- Controls ---
col1, col2, col3 = st.columns([2,2,2])
with col1:
    universe = st.selectbox("Select Universe", ["NIFTY 100", "Penny Stocks (₹<50)", "Both"])
with col2:
    period = st.select_slider("Prediction Period", options=list(['7 days', '15 days', '1 month', '3 months', '6 months', '12 months', '3 years', '5 years']), value="7 days")
with col3:
    invest = st.number_input("Investment per stock (₹)", value=100000, min_value=1000, step=1000)

# --- Stock Universe ---
NIFTY100 = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "ITC", "LT", "SBIN", "BHARTIARTL", "BAJFINANCE", "HINDUNILVR", "AXISBANK", "KOTAKBANK", "MARUTI", "SUNPHARMA", "HCLTECH", "ASIANPAINT", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "ONGC", "TATAMOTORS", "POWERGRID", "NTPC", "M&M", "ADANIENT", "ADANIPORTS", "JSWSTEEL", "TATASTEEL", "TECHM", "HDFCLIFE", "SBILIFE", "GRASIM", "COALINDIA", "BAJAJFINSV", "LTIM", "BRITANNIA", "BPCL", "CIPLA", "DIVISLAB", "HEROMOTOCO", "HINDALCO", "IOC", "INDUSINDBK", "DRREDDY", "BAJAJ-AUTO", "UPL", "EICHERMOT", "APOLLOHOSP", "TATACONSUM", "DLF", "PIDILITIND", "ICICIPRULI", "ICICIGI", "HAVELLS", "COLPAL", "NAUKRI", "LTTS", "MCDOWELL-N", "ADANIGREEN", "ABB", "BANKBARODA", "BEL", "BIOCON", "CHOLAFIN", "DABUR", "GAIL", "GODREJCP", "HINDPETRO", "INDIGO", "LICI", "MUTHOOTFIN", "PAGEIND", "PETRONET", "PIIND", "PNB", "RECLTD", "SBICARD", "SHREECEM", "SIEMENS", "SRF", "TATAPOWER", "TORNTPHARM", "TVSMOTOR", "VOLTAS", "ZOMATO", "JKCEMENT"]
def add_ns(symbol):
    # yfinance expects NSE tickers with '.NS'
    s = str(symbol).upper().replace(" ", "").replace("&","AND")
    if s.endswith(".NS"):
        return s
    return s + ".NS"

def get_universe(universe_choice):
    base = NIFTY100.copy()
    base_ns = [add_ns(s) for s in base]
    if universe_choice == "NIFTY 100":
        return base_ns
    elif universe_choice == "Penny Stocks (₹<50)":
        # We'll fetch a wider list: use NIFTY100 as placeholder and filter by price < 50
        return base_ns
    else:
        return base_ns

tickers = get_universe(universe)

# --- Fetch current prices ---
@st.cache_data(ttl=300)
def fetch_prices(tickers):
    data = yf.download(tickers=tickers, period="5d", interval="1d", threads=True, group_by='ticker', progress=False)
    latest = {}
    # yfinance returns a multi-index when multiple tickers; handle single vs multi
    for t in tickers:
        try:
            close_series = data[t]['Close']
        except Exception:
            # Single ticker case
            close_series = data['Close']
        if isinstance(close_series, pd.Series) and not close_series.empty:
            latest[t] = float(close_series.dropna().iloc[-1])
        else:
            latest[t] = np.nan
    return latest

prices = fetch_prices(tickers)

# --- Mock prediction function (realistic ranges) ---
np.random.seed(42)  # stable mock
def predict_return_pct(symbol, days):
    # Vol scales with time horizon (rough heuristic)
    annual_vol = 0.28  # 28% typical
    daily_vol = annual_vol / np.sqrt(252)
    horizon_vol = daily_vol * np.sqrt(max(days,1))
    # Drift ~ 6% annualized
    annual_drift = 0.06
    daily_drift = (1 + annual_drift)**(1/252) - 1
    mean = daily_drift * days
    # Random normal draw (stable per symbol+days using hash)
    rng = np.random.default_rng(abs(hash(symbol + str(days))) % (2**32))
    ret = rng.normal(loc=mean, scale=horizon_vol)
    # Clip to realistic bounds for the horizon
    clip_lo = -0.25 if days <= 30 else -0.40
    clip_hi = 0.25 if days <= 30 else 0.60
    ret = float(np.clip(ret, clip_lo, clip_hi))
    return round(ret * 100, 2)

# --- Build table ---
rows = []
days_map = {"7 days": 7, "15 days": 15, "1 month": 30, "3 months": 90, "6 months": 180, "12 months": 365, "3 years": 1095, "5 years": 1825}
for sym in tickers:
    price = prices.get(sym, np.nan)
    base_sym = sym.replace(".NS", "")
    days = days_map[period]
    pred_pct = predict_return_pct(base_sym, days)
    # Penny filter if needed
    include = True
    if universe == "Penny Stocks (₹<50)":
        include = (price <= 50) if price==price else False
    if universe == "Both":
        include = True
    if not include:
        continue
    projected = None
    qty = None
    if price and price==price and price>0:
        qty = invest / price
        projected = qty * price * (1 + pred_pct/100.0)
    rows.append({
        "Stock": base_sym,
        "Ticker": sym,
        "Current Price (₹)": None if pd.isna(price) else round(price, 2),
        "Predicted Return (%)": pred_pct,
        "Projected Value (₹)": None if projected is None else round(projected, 2),
        "Confidence (%)": int(65 + abs(hash(base_sym)) % 31)  # 65–95 mock
    })

df = pd.DataFrame(rows)

# --- Color helpers for AgGrid ---
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=False, sortable=True, filter=True)
# Fixed widths
gb.configure_column("Stock", width=160, pinned=True)
gb.configure_column("Ticker", width=130, pinned=True)
gb.configure_column("Current Price (₹)", width=150, type=['numericColumn','numberColumnFilter','customNumericFormat'], precision=2)
gb.configure_column("Predicted Return (%)", width=180, type=['numericColumn'], precision=2)
gb.configure_column("Projected Value (₹)", width=180, type=['numericColumn'], precision=2)
gb.configure_column("Confidence (%)", width=140, type=['numericColumn'])

# Default sort: highest predicted return
gb.configure_sorting([{
    "colId":"Predicted Return (%)",
    "sort":"desc"
}])

# Cell styles for gains/losses
neg_rule = {
    "condition": "params.value < 0",
    "style": {"color": "white", "backgroundColor": "#c0392b"}  # red
}
pos_rule = {
    "condition": "params.value >= 0",
    "style": {"color": "black", "backgroundColor": "#2ecc71"}  # green
}
gb.configure_column("Predicted Return (%)", cellStyleRules={
    "neg": neg_rule,
    "pos": pos_rule
})

grid_options = gb.build()

st.markdown(f"**Active period:** {period}  •  **Investment per stock:** ₹{invest:,}  •  **Rows:** {len(df)}")

AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.NO_UPDATE,
    theme="alpine",
    height=520,
    fit_columns_on_grid_load=False,
    allow_unsafe_jscode=True,
)

st.caption("Mock predictions use realistic ranges; live model (LSTM + fundamentals + sentiment) will replace this logic. Prices fetched via yfinance. Penny stocks defined as Current Price < ₹50.")
