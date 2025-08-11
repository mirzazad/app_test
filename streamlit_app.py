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

# --------------------------
# 📊 Bütün PYŞ'ler İçin 12 Aylık Kümülatif Net Giriş Grafik
# --------------------------

# Veri filtreleme (seçilen tarih aralığına göre)
df_filtered = main_df[(main_df["Tarih"].dt.date >= start_date) & 
                      (main_df["Tarih"].dt.date <= end_date)]

# Veriyi grupla ve 12 aylık kümülatif giriş hesaplama
if not df_filtered.empty:
    # 12 aylık kümülatif net giriş hesapla (başlangıç tarihinden itibaren)
    df_filtered = calculate_cumulative(df_filtered, ybb_start)  # Örnek: ybb_start tarihinden itibaren
    
    # Grafik oluştur
    fig3 = px.line(
        df_filtered,
        x='Tarih',
        y='Kümülatif Giriş',
        color='Varlık Sınıfı',  # Varlık sınıfı bazında renkli çizgiler
        title=f"Bütün PYŞ'ler İçin 12 Aylık Kümülatif Net Giriş - {start_date} - {end_date}",
        labels={"Kümülatif Giriş": "Kümülatif Giriş (M TL)", "Tarih": "Tarih"}
    )
    fig3.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Seçilen tarihlerde veri bulunamadı.")

