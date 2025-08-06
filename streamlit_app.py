import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from datetime import datetime, timedelta
import os
import gdown
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- Veriyi indir ---
@st.cache_data
def load_data():
url_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"
url = f"https://drive.google.com/uc?id={url_id}"
output = "main_df.pkl"
if not os.path.exists(output):
gdown.download(url, output, quiet=False)
return pd.read_pickle(output)

# --- Fonksiyon: PYŞ bazında fon akımı grafiği ---
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

if summary_df.empty:
st.warning("Grafik oluşturmak için yeterli veri yok.")
return

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

# --- Fonksiyon: Takasbank verisiyle varlık sınıfı değişimi grafiği ---
def show_takasbank_chart():
st.markdown("## 📊 Varlık Sınıfı Değişimi – Takasbank Verisi")

selected_date = st.date_input("Tarih seçin", datetime.today())
t_date = datetime.combine(selected_date, datetime.min.time())

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

try:
df_t = download_excel(t_date)
df_t7 = download_excel(t_date - timedelta(days=7))
df_t28 = download_excel(t_date - timedelta(days=28))
except Exception as e:
st.error(f"Veri çekilirken hata oluştu: {e}")
return

def extract_main(df):
df = df[df[df.columns[0]].isin(main_items)]
df = df.drop_duplicates(subset=[df.columns[0]])
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

buyukluk_serisi = extract_main(df_t).div(1e9).round(1)

df_pct = df_pct.merge(
buyukluk_serisi.rename("Büyüklük (mlr TL)"),
how="left",
left_on="Varlık Sınıfı",
right_index=True
)

fig = go.Figure()

fig.add_trace(go.Bar(
x=df_pct["Haftalık"],
y=df_pct["Varlık Sınıfı"],
name="Haftalık Değişim (bps)",
orientation="h",
marker_color="steelblue"
))

fig.add_trace(go.Bar(
x=df_pct["Aylık"],
y=df_pct["Varlık Sınıfı"],
name="Aylık Değişim (bps)",
orientation="h",
marker_color="lightblue"
))

fig.add_trace(go.Scatter(
x=df_pct["Büyüklük (mlr TL)"],
y=df_pct["Varlık Sınıfı"],
mode="markers",
name="Büyüklük (mlr TL)",
marker=dict(size=10, color="darkorange", symbol="circle"),
hovertemplate='<b>%{y}</b><br>Büyüklük: %{x:,.1f} mlr TL',
xaxis="x2",
showlegend=True
))

fig.update_layout(
title=f"📅 {t_date.strftime('%d %B %Y')} – Varlık Sınıfı Değişim & Büyüklük",
barmode="group",
xaxis=dict(
title="Değişim (bps)",
side="bottom",
showgrid=False
),
xaxis2=dict(
title="Büyüklük (mlr TL)",
overlaying="x",
side="top",
showgrid=False,
tickformat=","
),
yaxis=dict(title="Varlık Sınıfı"),
legend=dict(orientation="h", y=-0.2),
height=700,
plot_bgcolor="#f7f7f7",
paper_bgcolor="#ffffff",
font=dict(size=13, family="Segoe UI")
)

st.plotly_chart(fig, use_container_width=True, key="takasbank_chart")

def show_fon_turu_chart(t_date: datetime):
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
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
    plot_data = df_percent[["Haftalık Değ (bps)", "Aylık Değ (bps)"]].rename(columns={
        "Haftalık Değ (bps)": "Haftalık Değ",
        "Aylık Değ (bps)": "Aylık Değ"
    })
    t_amount_billion = df_combined.loc[sort_order, "t"] / 1e9

    turkish_months = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    t_plus_3 = t_date + timedelta(days=4)
    t_plus_3_str_tr = f"{t_plus_3.day} {turkish_months[t_plus_3.month]} {t_plus_3.year}"

    fig, ax1 = plt.subplots(figsize=(12, 10))
    plot_data.plot(kind="barh", ax=ax1, width=0.6, color={
        "Haftalık Değ": "#162336",
        "Aylık Değ": "#cc171d"
    })

    ax1.set_title(f"Fon Türü Bazında Değişim {t_plus_3_str_tr} itibari ile", fontsize=16)
    ax1.set_xlabel("Değişim (bps)", fontsize=13)
    ax1.set_ylabel("Fon Türü", fontsize=14)
    ax1.grid(axis="x", linestyle="--", alpha=0.6)
    ax1.legend(loc="center right")
    ax1.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f'))
    ax1.invert_yaxis()

    ax2 = ax1.twiny()
    ax2.scatter(t_amount_billion.values, range(len(t_amount_billion)), color="royalblue", marker="o", label="MLR TL")
    ax2.set_xlabel("Büyüklük (Milyar TL)")
    ax2.set_xlim(0, t_amount_billion.max() * 1.3)
    ax2.set_yticks(range(len(t_amount_billion)))
    ax2.set_yticklabels(df_percent.index.tolist())
    ax2.legend(loc="upper left")

    for i, value in enumerate(t_amount_billion.values):
        label = f"{int(round(value)):,}".replace(",", ".")
        ax2.text(value * 1.10, i, label, va='center', fontsize=12, color="#355765",
                 bbox=dict(boxstyle="round,pad=0.1", facecolor="#FFFFFF6F", edgecolor="none"))

    import streamlit as st
    st.pyplot(fig)



# --- Uygulama ---
st.sidebar.title("🧭 Sayfa Menüsü")
st.markdown("## Fon Akımları Paneli")
show_pysh_fund_flows()

st.markdown("---")

st.markdown("## Takasbank Paneli")
show_takasbank_chart()

st.markdown("## Fon Türü Paneli – Takasbank Verisi")
show_fon_turu_chart(t_date)
