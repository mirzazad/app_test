import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gdown
from datetime import datetime, timedelta
import OS
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

# Veriyi kontrol etme
st.write(main_df.head())  # Veriyi kontrol et

# --- Kümülatif Net Giriş Hesaplama --- 
def calculate_cumulative(df):
    """Verilen veriye kümülatif toplam uygular."""
    return df.cumsum()

def create_cumulative_plot(data, title="Kümülatif Net Giriş"):
    """Veriye kümülatif grafik çizer."""
    traces = []
    for column in data.columns:
        traces.append(
            go.Scatter(
                x=data.index,
                y=data[column],
                mode='lines',
                name=column
            )
        )

    layout = go.Layout(
        title=title,
        xaxis=dict(title='Tarih'),
        yaxis=dict(title='TRY'),
        hovermode='x unified',
        template='plotly_dark'
    )

    return go.Figure(data=traces, layout=layout)

# --- sum_per_date Hesaplama Fonksiyonu ---
def calculate_sum_per_date(df):
    """sum_per_date hesaplama"""
    columns_to_calculate = ['Yerli Hisse', 'TL Sabit Getirili', 'Döviz Sabit Getirili', 'Kıymetli Madenler', 
                            'Yabancı Hisse/BYF', 'TL Yatırım Fon/BYF', 'Teminat', 'Diğer', 'Para Piyasası']
    
    for col in columns_to_calculate:
        df[col + '_TL'] = (df[col] / 100) * df['Flow']
    
    tl_columns = [col + '_TL' for col in columns_to_calculate]
    sum_per_date = df.groupby('Tarih')[tl_columns].sum()
    sum_per_date.columns = [col.replace('_TL', '') for col in sum_per_date.columns]
    
    return sum_per_date

# --- Kümülatif Hesaplama --- 
sum_per_date = calculate_sum_per_date(main_df)
cumulative_data = calculate_cumulative(sum_per_date)

# --- Grafik Çizimi --- 
fig_ybb = create_cumulative_plot(cumulative_data, "12 Aylık Kümülatif Net Giriş")

# --- Streamlit Görselleştirme --- 
st.title("12 Aylık Kümülatif Net Giriş")
st.plotly_chart(fig_ybb, use_container_width=True)
