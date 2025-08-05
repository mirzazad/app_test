import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from datetime import datetime, timedelta
import os
import gdown



st.set_page_config(layout="wide")

# Veriyi indir
@st.cache_data
def load_data():
    url_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"
    if not os.path.exists(output):
        gdown.download(url, output, quiet=False)
    return pd.read_pickle(output)

# Fonksiyon: PYŞ bazında fon akımı grafiği
def show_pysh_fund_flows():
    main_df = load_data()

    st.title("📊 Fon Akımları Dashboard")

    main_df["Tarih"] = pd.to_datetime(main_df["Tarih"])
    asset_columns = [col for col in main_df.columns if col.endswith("_TL")]
    asset_columns_clean = [col.replace("_TL", "") for col in asset_columns]

    pysh_list = sorted(main_df["PYŞ"].dropna().unique())
    range_dict = {
        "1 Hafta": 5,
        "1 Ay": 22,
        "3 Ay": 66,
        "6 Ay": 126,
        "1 Yıl": 252
    }

    st.sidebar.header("Filtreler")
    selected_pysh = st.sidebar.selectbox("PYŞ seçin", pysh_list)
    selected_range = st.sidebar.selectbox("Zaman aralığı", list(range_dict.keys()))
    day_count = range_dict[selected_range]

    last_dates = main_df["Tarih"].drop_duplicates().sort_values(ascending=False).head(day_count)
    pysh_df = main_df[(main_df["PYŞ"] == selected_pysh) & (main_df["Tarih"].isin(last_dates))]
    total_flows = pysh_df[asset_columns].sum()

    summary_df = pd.DataFrame({
        "Varlık Sınıfı": asset_columns_clean,
        "Toplam Flow (mn)": total_flows.values / 1e6
    }).sort_values(by="Toplam Flow (mn)", ascending=False)
    total_sum_mn = summary_df["Toplam Flow (mn)"].sum()

    fig = px.bar(
        summary_df,
        x="Varlık Sınıfı",
        y="Toplam Flow (mn)",
        title=f"{selected_pysh} - {selected_range} Net Fon Akımı (Toplam: {total_sum_mn:,.1f} mn TL)",
        color_discrete_sequence=["#191970"]
    )

    fig.update_layout(
        title_font=dict(size=20, family="Segoe UI Semibold", color="black"),
        xaxis_title="Varlık Sınıfı",
        yaxis_title="Toplam Flow (mn)",
        yaxis_tickformat=",.0f",
        xaxis=dict(tickfont=dict(size=13, family="Segoe UI Semibold", color="black")),
        yaxis=dict(tickfont=dict(size=13, family="Segoe UI Semibold", color="black")),
        font=dict(size=13, family="Segoe UI", color="black"),
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


from datetime import datetime, timedelta
import io
import requests

# Fonksiyon: Takasbank verisiyle varlık sınıfı değişimi grafiği
def show_takasbank_chart():
    st.title("📊 Varlık Sınıfı Değişimi – Takasbank Verisi")

    # Tarih seçimi
    selected_date = st.date_input("Tarih seçin", datetime.today())
    t_date = datetime.combine(selected_date, datetime.min.time())

    # Ayarlar
    fon_grubu = "F"
    fon_turu = "99999"
    key = "rT4AQ2R2lXyX-Ys9LzTkPbJ8szIKc4w1xwMbqV-1v984zpEau4bixJOrFrmS9sM_0"
    main_items = [
        "Hisse Senedi", "Devlet Tahvili", "Finansman Bonosu", "Kamu Dış Borçlanma Araçları",
        "Özel Sektör Dış Borçlanma Araçları", "Takasbank Para Piyasası İşlemleri",
        "Kamu Kira Sertifikaları (Döviz)", "Özel Sektör Kira Sertifikaları", "Özel Sektör Yurt Dışı Kira Sertifikaları",
        "Vadeli Mevduat (Döviz)", "Katılma Hesabı (Döviz)", "Repo Islemleri", "Kıymetli Madenler",
        "Yabancı Borsa Yatırım Fonları", "Borsa Yatırım Fonları Katılma Payları", "Vadeli İşlemler Nakit Teminatları",
        "Diğer", "TOPLAM"
    ]

    @st.cache_data(show_spinner=False)
    def download_excel(date: datetime):
        date_str = date.strftime("%Y%m%d")
        url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=P&type={fon_grubu}&fundType={fon_turu}&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
        response = requests.get(url)
        return pd.read_excel(io.BytesIO(response.content))

    # Veri çekme
    try:
        df_t = download_excel(t_date)
        df_t7 = download_excel(t_date - timedelta(days=7))
        df_t28 = download_excel(t_date - timedelta(days=28))
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        st.stop()

    # Temizleme
    def extract_main(df):
        df = df[df[df.columns[0]].isin(main_items)]
        return df.set_index(df.columns[0])[df.columns[1]]

    df = pd.concat({
        "t": extract_main(df_t),
        "t7": extract_main(df_t7),
        "t28": extract_main(df_t28)
    }, axis=1)

    df = df.drop("TOPLAM")
    df_pct = df.div(df.sum(axis=0), axis=1)
    df_pct["Haftalık"] = (df_pct["t"] - df_pct["t7"]) * 10000
    df_pct["Aylık"] = (df_pct["t"] - df_pct["t28"]) * 10000
    df_pct = df_pct.round(1)
    df_pct = df_pct[["Haftalık", "Aylık"]].reset_index().rename(columns={df_pct.index.name: "Varlık Sınıfı"})

    fig = px.bar(
        df_pct.melt(id_vars="Varlık Sınıfı", value_vars=["Haftalık", "Aylık"]),
        x="value",
        y="Varlık Sınıfı",
        color="variable",
        orientation="h",
        labels={"value": "Değişim (bps)", "variable": "Dönem"},
        title=f"📅 {t_date.strftime('%d %B %Y')} – Haftalık & Aylık Varlık Sınıfı Değişimi (bps)"
    )

    fig.update_layout(
        barmode="group",
        xaxis_tickformat=",d",
        xaxis_title="Değişim (bps)",
        yaxis_title="",
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff",
        font=dict(size=13, family="Segoe UI", color="black"),
        legend_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

st.sidebar.title("🧭 Sayfa Menüsü")
selected_page = st.sidebar.radio("Görüntülemek istediğiniz paneli seçin:", ["Fon Akımları", "Takasbank Verisi"])

if selected_page == "Fon Akımları":
    show_pysh_fund_flows()
elif selected_page == "Takasbank Verisi":
    show_takasbank_chart()
