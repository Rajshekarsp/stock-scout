import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import joblib
import tensorflow as tf
from datetime import datetime, timedelta

# Load the trained LSTM model and scaler
@st.cache_resource
def load_model_and_scaler():
    model = tf.keras.models.load_model("lstm_stock_model.h5")
    scaler = joblib.load("scaler.pkl")
    return model, scaler

model, scaler = load_model_and_scaler()

# Function to fetch last 365 days of Reliance stock data
@st.cache_data
def get_stock_data(ticker="RELIANCE.NS", days=365):
    end = datetime.now()
    start = end - timedelta(days=days)
    data = yf.download(ticker, start=start, end=end)
    return data

# Prepare data for prediction
def prepare_data(data, scaler, time_step=60):
    close_prices = data['Close'].values.reshape(-1, 1)
    scaled_data = scaler.transform(close_prices)

    x_input = scaled_data[-time_step:].reshape(1, time_step, 1)
    return x_input

# Predict next day price
def predict_next_day(model, scaler, data):
    x_input = prepare_data(data, scaler)
    prediction_scaled = model.predict(x_input)
    prediction = scaler.inverse_transform(prediction_scaled)
    return prediction[0][0]

# Streamlit UI
st.title("📈 Reliance Stock Price Predictor")
st.write("This app predicts the next day's closing price for Reliance Industries Limited (NSE: RELIANCE.NS) using a trained LSTM model.")

# Fetch and display last 365 days data
data = get_stock_data("RELIANCE.NS", 365)
st.subheader("Last 365 Days Stock Data")
st.line_chart(data['Close'])

# Predict next day price
if st.button("Predict Next Day Price"):
    predicted_price = predict_next_day(model, scaler, data)
    st.success(f"Predicted Closing Price for Next Day: ₹{predicted_price:.2f}")

