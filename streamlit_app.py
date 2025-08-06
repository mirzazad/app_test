import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import gdown
import os
import io
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# --------------------------
# 📅 Ortak tarih seçimi (sidebar)
# --------------------------
t_date = pd.to_datetime(
    st.sidebar.date_input("Tarih seçin", pd.to_datetime("today"))
)

# --------------------------
# 📦 PYŞ bazında fon akımı verisi
# --------------------------
@st.cache_data

def load_data():
    url_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"
    if not os.path.exists(output):
        gdown.download(url, output, quiet=False)
    return pd.read_pickle(output)

def show_pysh_fund_flows():
    main_df = load_data()
    st.markdown("## 📊 Fon Akımları Dashboard")

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

    selected_pysh = st.selectbox("PYŞ seçin", pysh_list, key="pysh")
    selected_range = st.selectbox("Zaman aralığı", list(range_dict.keys()), key="range")
    day_count = range_dict[selected_range]

    last_dates = main_df["Tarih"].drop_duplicates().sort_values(ascending=False).head(day_count)
    pysh_df = main_df[(main_df["PYŞ"] == selected_pysh) & (main_df["Tarih"].isin(last_dates))]

    if pysh_df.empty:
        st.warning("Seçilen kriterlere göre veri bulunamadı.")
        return

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
        font=dict(size=13, family="Segoe UI", color="black"),
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# 📊 Takasbank - Varlık Sınıfı Paneli
# --------------------------
def show_fon_turu_chart(t_date: datetime):
    st.markdown("## 📊 Fon Türü Paneli – Takasbank Verisi")

    import requests
    import pandas as pd
    import plotly.graph_objects as go
    from datetime import timedelta
    from io import BytesIO

    categories_of_interest = [
        "Altın Fonu", "Altın Katılım Fonu", "Borçlanma Araçları Fonu", "Borçlanma Araçları Özel Fon",
        "Değişken Döviz Fon", "Değişken Fon", "Değişken Özel Fon", "Diğer Değişken Fon",
        "Endeks Hisse Senedi Fonu", "Eurobond Borçlanma Araçları Fonu", "Fon Sepeti Fonu",
        "Fon Sepeti Özel Fonu", "Fon Sepeti Serbest Fon", "Hisse Senedi Fonu",
        "Hisse Senedi Serbest Fon", "Hisse Senedi Serbest Özel Fon", "Karma Fon",
        "Katılım Döviz Fon", "Katılım Fonu", "Katılım Hisse Senedi Fonu",
        "Katılım Serbest Döviz Özel Fon", "Katılım Serbest Fon", "Katılım Serbest Özel Fon",
        "Kısa Vadeli Borçlanma Araçları Fonu", "Kısa Vadeli Katılım Serbest Fon",
        "Kısa Vadeli Kira Sertifikası Katılım", "Kısa Vadeli Serbest  Fon",
        "Kira Sertifikası Katılım Fonu", "Orta Vadeli Borçlanma Araçları Fonu",
        "Özel Sektör Borçlanma Araçları Fonu", "Para Piyasası Fonu", "Para Piyasası Katılım Fonu",
        "Serbest Döviz Fon", "Serbest Döviz Özel Fon", "Serbest Fon", "Serbest Özel Fon",
        "Uzun Vadeli Borçlanma Araçları Fonu", "Yabancı Borçlanma Araçları Fonu",
        "Yabancı Fon Sepeti Fonu", "Yabancı Hisse Senedi Fonu"
    ]

    key = "rT4AQ2R2lXyX-Ys9LzTkPbJ8szIKc4w1xwMbqV-1v9-LnLjLKETltBqStY7ldLOK0"
    dates = {
        "t": t_date,
        "t7": t_date - timedelta(days=7),
        "t28": t_date - timedelta(days=28)
    }

    data = {}
    for label, date in dates.items():
        date_str = date.strftime("%Y%m%d")
        url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=F&type=F&fundType=99999&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
        response = requests.get(url)
        df = pd.read_excel(BytesIO(response.content))
        df = df[df[df.columns[0]].isin(categories_of_interest)].set_index(df.columns[0])
        data[label] = df[df.columns[1]]

    df_combined = pd.concat(data.values(), axis=1)
    df_combined.columns = data.keys()
    df_combined.loc["TOPLAM"] = df_combined.sum()

    df_percent = df_combined.drop("TOPLAM").div(df_combined.loc["TOPLAM"], axis=1)
    df_percent["Haftalık Değ (bps)"] = (df_percent["t"] - df_percent["t7"]) * 10000
    df_percent["Aylık Değ (bps)"] = (df_percent["t"] - df_percent["t28"]) * 10000
    df_percent = df_percent.round(1)

    sort_order = df_combined.drop("TOPLAM")["t"].sort_values(ascending=False).index
    df_percent = df_percent.loc[sort_order]
    t_amount_billion = df_combined.loc[sort_order, "t"] / 1e9

    df_plot = df_percent[["Haftalık Değ (bps)", "Aylık Değ (bps)"]].copy()
    df_plot["Büyüklük (mlr TL)"] = t_amount_billion
    df_plot = df_plot.reset_index().rename(columns={"index": "Fon Türü"})

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_plot["Haftalık Değ (bps)"],
        y=df_plot["Fon Türü"],
        name="Haftalık",
        orientation="h",
        marker_color="#162336"
    ))

    fig.add_trace(go.Bar(
        x=df_plot["Aylık Değ (bps)"],
        y=df_plot["Fon Türü"],
        name="Aylık",
        orientation="h",
        marker_color="#cc171d"
    ))

    fig.add_trace(go.Scatter(
        x=df_plot["Büyüklük (mlr TL)"],
        y=df_plot["Fon Türü"],
        mode="markers+text",
        name="Büyüklük",
        marker=dict(size=10, color="darkorange", symbol="circle"),
        text=[f"{x:.1f}" for x in df_plot["Büyüklük (mlr TL)"]],
        textposition="middle right",
        xaxis="x2",
        showlegend=True
    ))

    fig.update_layout(
        title=f"Fon Türü Bazında Değişim ve Büyüklük – {t_date.strftime('%d %B %Y')}",
        barmode="group",
        height=700,
        xaxis=dict(title="Değişim (bps)", side="bottom"),
        xaxis2=dict(
            title="Büyüklük (mlr TL)",
            overlaying="x",
            side="top",
            tickformat=",.0f"
        ),
        yaxis=dict(title="Fon Türü"),
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff",
        font=dict(size=13, family="Segoe UI"),
        legend=dict(orientation="h", y=-0.2)
    )

    st.plotly_chart(fig, use_container_width=True)


# --------------------------
# ⛳ Uygulama Gövdesi
# --------------------------
st.markdown("## Fon Akımları Paneli")
show_pysh_fund_flows()

st.markdown("---")

st.markdown("## Takasbank Paneli")
show_takasbank_chart()
