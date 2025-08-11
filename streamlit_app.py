import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os
from datetime import datetime, timedelta

# --- Veriyi indir ---
@st.cache_data
def load_data():
    url_id = "1b6-R6zQXRcOW7OI9ZcWoIcZuAK6OlgT4"
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"

    if not os.path.exists(output):
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
    # 📈 Fon Akımları Grafiği
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
        font=dict(
            size=13,
            family="Segoe UI",
            color="black"
        ),
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# 📊 Kümülatif 12 Aylık Net Giriş
# --------------------------

def calculate_12_months_cumulative(df):
    """12 aylık kümülatif net giriş hesaplama."""
    df_sorted = df.sort_values('Tarih')
    df_sorted['Kümülatif Giriş'] = df_sorted['Toplam Flow (mn)'].rolling(window=252).sum()  # 252 iş günü yaklaşık 12 ay
    return df_sorted

# Veri filtreleme (seçilen PYŞ ve tarih aralığına göre)
df_filtered = main_df[(main_df["Tarih"].dt.date >= start_date) & 
                      (main_df["Tarih"].dt.date <= end_date) &
                      (main_df["PYŞ"] == selected_pysh)]

# Veriyi grupla ve 12 aylık kümülatif giriş hesaplama
if not df_filtered.empty:
    df_filtered['Toplam Flow (mn)'] = df_filtered[asset_columns].sum(axis=1)
    
    # 12 aylık kümülatif net giriş hesapla
    df_filtered = calculate_12_months_cumulative(df_filtered)
    
    # Grafik oluştur
    fig3 = px.line(
        df_filtered,
        x='Tarih',
        y='Kümülatif Giriş',
        title=f"{selected_pysh} 12 Aylık Kümülatif Net Giriş - {start_date} - {end_date}",
        labels={"Kümülatif Giriş": "Kümülatif Giriş (M TL)", "Tarih": "Tarih"}
    )
    fig3.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Seçilen tarihlerde veri bulunamadı.")
