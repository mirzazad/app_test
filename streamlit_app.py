import os  # os modülünü ekleyin
import gdown
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- Veriyi indir ---
@st.cache_data
def load_data():
    url_id = "1b6-R6zQXRcOW7OI9ZcWoIcZuAK6OlgT4"  # Google Drive dosyasının ID'si
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"

    if not os.path.exists(output):  # sadece ilk sefer indirir
        gdown.download(url, output, quiet=False)
    return pd.read_pickle(output)

main_df = load_data()

# --- Veri kontrolü ---
st.write(main_df.head())  # Veriyi kontrol et
