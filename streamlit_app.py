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

import pandas as pd
import streamlit as st

# --- Haftalık Giriş Yapan Fonlar --- 
def prepare_weekly_inflow(df, top_n=10):
    # Son 5 gün verisini al
    df_sorted = df.sort_values('Tarih', ascending=False)
    last_5_days = df_sorted.head(5)

    # Fon bazında toplam akımı hesapla
    weekly_inflow = last_5_days.groupby('Fon Kodu')['Flow'].sum().div(1_000_000).round(1).reset_index()

    # En yüksek 10 fonu seç
    top_funds = weekly_inflow.sort_values('Flow', ascending=False).head(top_n)
    return top_funds

# --- Streamlit İçin Görselleştirme --- 
st.title("Haftalık En Büyük Giriş Yapan Fonlar")

# Veriyi işleyelim
top_funds_weekly = prepare_weekly_inflow(main_df)

# Eğer veriler varsa, tabloyu ve grafiği gösterelim
if not top_funds_weekly.empty:
    st.subheader("Haftalık En Büyük Giriş Yapan Fonlar")
    st.write(top_funds_weekly)

    # Burada grafiği eklemek isterseniz, örneğin Plotly kullanarak:
    import plotly.express as px
    fig = px.bar(top_funds_weekly, x='Fon Kodu', y='Flow', title="Haftalık En Büyük Giriş Yapan Fonlar")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Seçilen tarihlerde veri bulunamadı.")
