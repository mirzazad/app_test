import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from io import BytesIO

# --- Veriyi indir ---
@st.cache_data
def load_data():
    url_id = "1b6-R6zQXRcOW7OI9ZcWoIcZuAK6OlgT4"  # kendi dosya ID'ni buraya yaz
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"

    if not os.path.exists(output):  # sadece ilk sefer indirir
        gdown.download(url, output, quiet=False)
    return pd.read_pickle(output)

main_df = load_data()

file_id = '1e3OE8r7ZuYe5vvOKPR9_TjuMNyDdLx2r'  # Google Drive dosyasının ID'si
url = f"https://drive.google.com/uc?id={file_id}"

# Dosyayı indir
output = 'fund_infox.xlsx'
gdown.download(url, output, quiet=False)

# Excel dosyasını pandas ile oku
fund_info = pd.read_excel(output)

# --------------------------
# 🔍 Filtreleme ayarları
# --------------------------
main_df["Tarih"] = pd.to_datetime(main_df["Tarih"])
asset_columns = [col for col in main_df.columns if col.endswith("_TL")]
asset_columns_clean = [col.replace("_TL", "") for col in asset_columns]

pysh_list = sorted(main_df["PYŞ"].dropna().unique())

# --------------------------
# 🧭 Sidebar - Tarih Seçimi
# --------------------------
st.sidebar.header("Filtreler")
selected_pysh = st.sidebar.selectbox("PYŞ seçin", pysh_list)

# Get available dates from the dataset
available_dates = main_df["Tarih"].drop_duplicates().sort_values()

# Custom date range selection limited to the available dates in the dataset
start_date = st.sidebar.date_input("Başlangıç Tarihi", available_dates.min())
end_date = st.sidebar.date_input("Bitiş Tarihi", available_dates.max())

# --------------------------
# 📊 Veri Hazırlığı
# --------------------------
# Filter data based on selected dates
pysh_df = main_df[(main_df["PYŞ"] == selected_pysh) & 
                  (main_df["Tarih"] >= pd.to_datetime(start_date)) & 
                  (main_df["Tarih"] <= pd.to_datetime(end_date))]

if pysh_df.empty:
    st.warning("Seçilen tarihlerde veri bulunamadı.")
else:
    total_flows = pysh_df[asset_columns].sum()

    summary_df = pd.DataFrame({
        "Varlık Sınıfı": asset_columns_clean,
        "Toplam Flow (mn)": total_flows.values / 1e6
    }).sort_values(by="Toplam Flow (mn)", ascending=False)

    total_sum_mn = summary_df["Toplam Flow (mn)"].sum()

    # --------------------------
    # 📈 Grafik
    # --------------------------
    fig = px.bar(
        summary_df,
        x="Varlık Sınıfı",
        y="Toplam Flow (mn)",
        title=f"{selected_pysh} - {start_date} - {end_date} Net Fon Akımı (Toplam: {total_sum_mn:,.1f} mn TL)",
        color_discrete_sequence=["#191970"]
    )

    fig.update_layout(
        title_font=dict(size=20, family="Segoe UI Semibold", color="black"),
        xaxis_title="Varlık Sınıfı",
        yaxis_title="Toplam Flow (mn)",
        yaxis_tickformat=",.0f",
        xaxis=dict(
            tickfont=dict(size=13, family="Segoe UI Semibold", color="black")
        ),
        yaxis=dict(
            tickfont=dict(size=13, family="Segoe UI Semibold", color="black")
        ),
        font=dict(
            size=13,
            family="Segoe UI",
            color="black"
        ),
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff"
    )

    # --------------------------
    # 🖥️ Sayfa Gösterimi
    # --------------------------
    st.title("Fon Akımları Dashboard")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# 📊 Kümülatif Net Giriş Grafik
# --------------------------

# Veri filtreleme
df_filtered = main_df[(main_df["Tarih"].dt.date >= start_date) & 
                      (main_df["Tarih"].dt.date <= end_date) &
                      (main_df["PYŞ"] == selected_pysh)]

# Veriyi grupla ve işle
if not df_filtered.empty:
    daily = df_filtered.groupby("Tarih")[asset_columns].sum().div(1_000_000).round(2)
    daily["Toplam"] = daily.sum(axis=1).round(2)
    daily["Kümülatif Giriş"] = daily["Toplam"].cumsum()

    # Grafik oluştur
    fig2 = px.line(
        daily,
        x=daily.index,
        y="Kümülatif Giriş",
        title=f"{selected_pysh} Kümülatif Net Giriş - {start_date} - {end_date}",
        labels={"value": "Kümülatif Giriş (M TL)", "Tarih": "Tarih"}
    )

    fig2.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.warning("Seçilen tarihlerde veri bulunamadı.")

# --------------------------
# 📊 Bütün PYŞ'ler İçin 12 Aylık Kümülatif Net Giriş Grafik
# --------------------------

# --- Kümülatif Net Giriş Hesaplama (Başlangıç Tarihi Bazında) ---
def calculate_cumulative(df, start_date):
    """Başlangıç tarihinden itibaren kümülatif net giriş hesaplama."""
    df_filtered = df[df['Tarih'] >= pd.to_datetime(start_date)]  # Başlangıç tarihinden sonrası
    df_filtered['Toplam Flow (mn)'] = df_filtered[asset_columns].sum(axis=1)  # Toplam akımları hesapla
    df_filtered['Kümülatif Giriş'] = df_filtered['Toplam Flow (mn)'].cumsum()  # Kümülatif birikim hesapla
    return df_filtered

from datetime import datetime, timedelta

import plotly.graph_objects as go

# Yüklenen veriyi almak
main_df = load_data()

# --- Varlık Sınıfı Bazında Akımların Hesaplanması ---
def calculate_flow(df):
    """Bu fonksiyon, her fon için flow hesaplar."""
    df['Flow'] = df['Yerli Hisse'] + df['TL Sabit Getirili'] + df['Döviz Sabit Getirili']  # Örnek hesaplama
    return df

# --- sum_per_date Hesaplama Fonksiyonu ---
def calculate_sum_per_date(df):
    """sum_per_date hesaplama"""
    # Varlık sınıfı bazında akımları hesapla ve sum_per_date oluştur
    columns_to_calculate = ['Yerli Hisse', 'TL Sabit Getirili', 'Döviz Sabit Getirili', 'Kıymetli Madenler', 
                            'Yabancı Hisse/BYF', 'TL Yatırım Fon/BYF', 'Teminat', 'Diğer', 'Para Piyasası']
    
    for col in columns_to_calculate:
        df[col + '_TL'] = (df[col] / 100) * df['Flow']
    
    tl_columns = [col + '_TL' for col in columns_to_calculate]
    sum_per_date = df.groupby('Tarih')[tl_columns].sum()
    sum_per_date.columns = [col.replace('_TL', '') for col in sum_per_date.columns]
    
    return sum_per_date

# --- Kümülatif Hesaplama Fonksiyonu ---
def calculate_cumulative(data):
    """Verilen veriye kümülatif toplam uygular."""
    return data.cumsum()

# --- Kümülatif Grafik Çizim Fonksiyonu ---
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
    
    annotations = []
    for column in data.columns:
        val = data[column].iloc[-1] / 1_000_000_000  # Milyar olarak
        annotations.append(dict(
            x=data.index[-1], y=data[column].iloc[-1],
            text=f'{val:.1f} Milyar',
            showarrow=True, arrowhead=3
        ))

    layout = go.Layout(
        title=title,
        xaxis=dict(title='Tarih'),
        yaxis=dict(title='TRY'),
        hovermode='x unified',
        template='plotly_dark'
    )

    return go.Figure(data=traces, layout=layout)

# --- Veri Hazırlığı ve Grafik Oluşumu ---
if main_df is not None:
    # `main_df` üzerinde işlem yaparak sum_per_date oluşturuluyor
    sum_per_date = calculate_sum_per_date(main_df)
    
    # 12 Aylık Kümülatif Net Giriş Hesaplama
    cumulative_data = calculate_cumulative(sum_per_date)

    # Grafik oluştur
    fig_ybb = create_cumulative_plot(cumulative_data, "12 Aylık Kümülatif Net Giriş")

    # --- Streamlit ile görselleştirme ---
    st.title("Kümülatif 12 Aylık Net Giriş")
    st.plotly_chart(fig_ybb, use_container_width=True)
else:
    st.warning("Veri bulunamadı. Lütfen pickle dosyasının doğru yolda olduğundan emin olun.")

import gdown
import pandas as pd
import streamlit as st

# --- Google Drive'dan Excel Dosyasını İndirme --- 


import pandas as pd

# --- Fon adı filtreleme fonksiyonları ---
def filter_exclude_para(df):
    return df[~df['Fon Adı'].str.contains('Para', case=False, na=False)]

def filter_exclude_serbest(df):
    return df[~df['Fon Adı'].str.contains('Serbest', case=False, na=False)]

def filter_yogun_only(df):
    return df[df['Fon Adı'].str.contains('Yoğun', case=False, na=False)]

# --- Haftalık ve Aylık giriş ve çıkışları hesaplayan fonksiyon ---
def prepare_flow_table(df, period_tail, period_name, ascending=False):
    """Haftalık ve Aylık Giriş/Çıkışları hesapla ve sıralama yap."""
    df_sorted = df.sort_values(['Fon Kodu', 'Tarih'])
    recent = df_sorted.groupby('Fon Kodu').tail(period_tail)
    aggregated = (
        recent.groupby('Fon Kodu')['Flow'].sum()  # Toplam Giriş/Çıkış
        .div(1_000_000).round(1)  # Milyon TL cinsinden
        .reset_index()
        .sort_values('Flow', ascending=ascending)  # Giriş/Çıkışa göre sıralama
    )
    aggregated[period_name] = aggregated['Flow'].apply(lambda x: f"{x:,.0f} M TL")
    return aggregated

# --- Haftalık ve Aylık giriş/çıkış hesaplamaları ---
weekly_inflow = prepare_flow_table(main_df, period_tail=5, period_name='Haftalık_Giriş')
weekly_outflow = prepare_flow_table(main_df, period_tail=5, period_name='Haftalık_Çıkış', ascending=True)
monthly_inflow = prepare_flow_table(main_df, period_tail=22, period_name='Aylık_Giriş')
monthly_outflow = prepare_flow_table(main_df, period_tail=22, period_name='Aylık_Çıkış', ascending=True)

# --- En Büyük 10 Giriş ve Çıkışı bulma ---
def get_top_10_greatest_flow(df, period_name):
    """Fonlar arasında en büyük 10 giriş/çıkışı bul."""
    return df.nlargest(10, period_name)[['Fon Adı', period_name]]

# --- Filtrelemeleri ve sıralamaları yapmak ---
filtered_weekly_inflow = filter_yogun_only(weekly_inflow)  # Yoğun fonlar sadece
filtered_monthly_inflow = filter_yogun_only(monthly_inflow)

# Haftalık ve Aylık en büyük 10 giriş
top_10_weekly_inflow = get_top_10_greatest_flow(filtered_weekly_inflow, 'Haftalık_Giriş')
top_10_monthly_inflow = get_top_10_greatest_flow(filtered_monthly_inflow, 'Aylık_Giriş')

# Haftalık ve Aylık en büyük 10 çıkış
top_10_weekly_outflow = get_top_10_greatest_flow(filtered_weekly_outflow, 'Haftalık_Çıkış')
top_10_monthly_outflow = get_top_10_greatest_flow(filtered_monthly_outflow, 'Aylık_Çıkış')

# --- Sonuçları Gösterme (Streamlit'te) ---
st.write("Haftalık En Büyük 10 Giriş Fonları:")
st.write(top_10_weekly_inflow)

st.write("Aylık En Büyük 10 Giriş Fonları:")
st.write(top_10_monthly_inflow)

st.write("Haftalık En Büyük 10 Çıkış Fonları:")
st.write(top_10_weekly_outflow)

st.write("Aylık En Büyük 10 Çıkış Fonları:")
st.write(top_10_monthly_outflow)



