import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os

@st.cache_data
def load_data():
    url_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"  # kendi dosya ID'ni buraya yaz
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

# Custom date range selection
start_date = st.sidebar.date_input("Başlangıç Tarihi", datetime.today() - timedelta(days=30))
end_date = st.sidebar.date_input("Bitiş Tarihi", datetime.today())

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
