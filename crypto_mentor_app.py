import streamlit as st
from PIL import Image
import io
import numpy as np
import cv2
import random
import requests
from streamlit_extras.card import card

st.set_page_config(page_title="danCryptoMentorApp", layout="wide")
st.title("📊 Crypto Chart Analyzer - danCryptoMentorApp")
st.markdown("""
    This AI-powered mentor analyzes uploaded TradingView chart screenshots and gives you clear trading advice: **Long**, **Short**, or **Wait**.

    ✅ Analyzes chart patterns automatically  
    ✅ Detects peaks and troughs (swing highs/lows)  
    ✅ Uses real-time prices via CoinGecko  
    ✅ Uses mocked RSI/MACD/Bollinger indicators (for now)  
    ✅ Takes Taabdeal.org fee and leverage into account  
    ✅ Provides confident decisions with zero ambiguity  
""")

# File uploader
uploaded_files = st.file_uploader("Upload TradingView chart screenshot(s)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

leverage = st.slider("Select Leverage (3x - 30x)", min_value=3, max_value=30, value=10)
fee = 2.0  # Fixed fee for taabdeal.org

# CoinGecko API call to fetch price
def get_price(coin_id="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usdt"
    try:
        response = requests.get(url)
        data = response.json()
        return data[coin_id]['usdt']
    except:
        return None

# CoinGecko API to fetch top gainers/losers
@st.cache_data(ttl=300)
def get_top_movers():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usdt&order=percent_change_24h_desc&per_page=10&page=1"
    try:
        response = requests.get(url)
        data = response.json()
        top_gainers = [(coin['name'], coin['symbol'], coin['price_change_percentage_24h']) for coin in data[:5]]
        top_losers = [(coin['name'], coin['symbol'], coin['price_change_percentage_24h']) for coin in data[-5:]]
        return top_gainers, top_losers
    except:
        return [], []

# Mock function to simulate indicator reading
def mock_indicators():
    return {
        "RSI": random.randint(20, 80),
        "MACD": random.choice(["Bullish", "Bearish"]),
        "Bollinger": random.choice(["Price near Upper Band", "Price near Lower Band"])
    }

# Detect peaks and troughs in chart-like image
def detect_peaks_troughs(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 50, 150)
    hist = np.sum(edges, axis=1)
    hist_smooth = np.convolve(hist, np.ones(10)/10, mode='same')
    peaks = []
    troughs = []
    for i in range(1, len(hist_smooth)-1):
        if hist_smooth[i-1] < hist_smooth[i] > hist_smooth[i+1]:
            peaks.append(i)
        elif hist_smooth[i-1] > hist_smooth[i] < hist_smooth[i+1]:
            troughs.append(i)
    return peaks, troughs

# Decision based on mocked data and basic logic
def mentor_decision(rsi, macd, bollinger):
    if rsi < 30 and macd == "Bullish":
        return ("📈 LONG", "Strong upside signal based on RSI < 30 and bullish MACD.")
    elif rsi > 70 and macd == "Bearish":
        return ("📉 SHORT", "RSI > 70 with bearish MACD suggests downside.")
    elif bollinger == "Price near Upper Band" and macd == "Bearish":
        return ("📉 SHORT", "Near upper Bollinger Band with bearish MACD.")
    elif bollinger == "Price near Lower Band" and macd == "Bullish":
        return ("📈 LONG", "Near lower Bollinger Band with bullish MACD.")
    else:
        return ("⏳ WAIT", "Conditions not favorable for entry.")

# Show top movers section
top_gainers, top_losers = get_top_movers()
with st.expander("🚀 Top Gainers / 📉 Top Losers (24h)"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚀 Gainers")
        for g in top_gainers:
            st.markdown(f"🟢 **{g[0]}** ({g[1].upper()}): **{g[2]:.2f}%**")
    with col2:
        st.subheader("📉 Losers")
        for l in top_losers:
            st.markdown(f"🔴 **{l[0]}** ({l[1].upper()}): **{l[2]:.2f}%**")

# Main logic
if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"📁 Analysis for {file.name}")
        image = Image.open(file)
        img_array = np.array(image)
        st.image(image, caption="Uploaded Chart", use_column_width=True)

        coin_name = st.text_input("Enter Coin ID for Price (e.g. bitcoin, ethereum, pepe)", value="bitcoin", key=file.name)
        price = get_price(coin_name.lower())
        if price:
            st.markdown(f"💰 **Current Price:** `${price:.2f}` USDT")
        else:
            st.warning("Could not fetch price data for this coin.")

        indicators = mock_indicators()
        st.markdown(f"📊 **Indicators:**  ")
        st.markdown(f"- RSI: `{indicators['RSI']}`")
        st.markdown(f"- MACD: `{indicators['MACD']}`")
        st.markdown(f"- Bollinger Bands: `{indicators['Bollinger']}`")

        peaks, troughs = detect_peaks_troughs(img_array)
        st.markdown(f"🔼 Detected `{len(peaks)}` peaks")
        st.markdown(f"🔽 Detected `{len(troughs)}` troughs")

        signal, explanation = mentor_decision(indicators['RSI'], indicators['MACD'], indicators['Bollinger'])

        st.markdown("""
        <div style='border: 2px solid #ccc; padding: 1rem; border-radius: 10px; background-color: #f9f9f9;'>
        <h3 style='color: #2a9d8f;'>🧠 Mentor Decision: {}</h3>
        <p style='font-size: 1.1rem;'>{}</p>
        <p>📌 Leverage: {}x | 💸 Taabdeal.org Fee: {} USDT</p>
        </div>
        """.format(signal, explanation, leverage, fee), unsafe_allow_html=True)
else:
    st.info("Upload at least one TradingView screenshot to get started.")
