import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import io
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# --- Ortak tarih seçimi ---
st.sidebar.title("🧭 Sayfa Menüsü")
selected_date = st.sidebar.date_input("Tarih seçin", datetime.today())
t_date = datetime.combine(selected_date, datetime.min.time())

# --- Takasbank Varlık Sınıfı Paneli ---
def show_takasbank_chart(t_date):
    st.markdown("## 📊 Varlık Sınıfı Değişimi – Takasbank Verisi")

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

    def download_excel(date):
        date_str = date.strftime("%Y%m%d")
        url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=P&type={fon_grubu}&fundType={fon_turu}&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
        response = requests.get(url)
        return pd.read_excel(io.BytesIO(response.content))

    def extract_main(df):
        df = df[df[df.columns[0]].isin(main_items)]
        df = df.drop_duplicates(subset=[df.columns[0]])
        return df.set_index(df.columns[0])[df.columns[1]]

    try:
        df_t = extract_main(download_excel(t_date))
        df_t7 = extract_main(download_excel(t_date - timedelta(days=7)))
        df_t28 = extract_main(download_excel(t_date - timedelta(days=28)))
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        return

    df = pd.concat({"t": df_t, "t7": df_t7, "t28": df_t28}, axis=1)
    df = df.drop("TOPLAM")
    df_pct = df.div(df.sum(axis=0), axis=1)
    df_pct["Haftalık"] = (df_pct["t"] - df_pct["t7"]) * 10000
    df_pct["Aylık"] = (df_pct["t"] - df_pct["t28"]) * 10000
    df_pct = df_pct.round(1)

    df_pct = df_pct.reset_index().rename(columns={df_pct.columns[0]: "Varlık Sınıfı"})
    buyukluk = df_t.div(1e9).round(1)
    df_pct = df_pct.merge(buyukluk.rename("Büyüklük (mlr TL)"), left_on="Varlık Sınıfı", right_index=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_pct["Haftalık"],
        y=df_pct["Varlık Sınıfı"],
        name="Haftalık Değişim (bps)",
        orientation="h",
        marker_color="#1f77b4"
    ))

    fig.add_trace(go.Bar(
        x=df_pct["Aylık"],
        y=df_pct["Varlık Sınıfı"],
        name="Aylık Değişim (bps)",
        orientation="h",
        marker_color="#aec7e8"
    ))

    fig.add_trace(go.Scatter(
        x=df_pct["Büyüklük (mlr TL)"],
        y=df_pct["Varlık Sınıfı"],
        mode="markers",
        name="Büyüklük",
        marker=dict(size=10, color="darkorange", symbol="circle"),
        xaxis="x2",
        hovertemplate="<b>%{y}</b><br>Büyüklük: %{x:.1f} mlr TL"
    ))

    fig.update_layout(
        barmode="group",
        title=f"📅 {t_date.strftime('%d %B %Y')} – Varlık Sınıfı Değişim ve Büyüklük",
        xaxis=dict(title="Değişim (bps)", side="bottom"),
        xaxis2=dict(title="Büyüklük (mlr TL)", overlaying="x", side="top"),
        yaxis=dict(title="Varlık Sınıfı"),
        height=700,
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff",
        font=dict(size=13, family="Segoe UI")
    )

    st.plotly_chart(fig, use_container_width=True, key="takasbank")

# --- Sayfa ---
st.markdown("## Fon Akımları Paneli")
show_takasbank_chart(t_date)
