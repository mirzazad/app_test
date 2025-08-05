import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📊 Varlık Sınıfı Değişimi – Takasbank Verisi")

# -- Tarih seçimi
selected_date = st.date_input("Tarih seçin", datetime.today())
t_date = datetime.combine(selected_date, datetime.min.time())

# -- Ayarlar
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

# -- Excel indir
@st.cache_data(show_spinner=False)
def download_excel(date: datetime):
    date_str = date.strftime("%Y%m%d")
    url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=P&type={fon_grubu}&fundType={fon_turu}&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
    response = requests.get(url)
    return pd.read_excel(io.BytesIO(response.content))

# -- Veri çekme
try:
    df_t = download_excel(t_date)
    df_t7 = download_excel(t_date - timedelta(days=7))
    df_t28 = download_excel(t_date - timedelta(days=28))
except Exception as e:
    st.error(f"Veri çekilirken hata oluştu: {e}")
    st.stop()

# -- Temizleme
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

# -- Interaktif Plotly bar chart
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
