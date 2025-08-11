import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime, timedelta
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- Veriyi indir ---
@st.cache_data
def load_data(t_date):
    categories_of_interest = [
        "Altın Fonu", "Altın Katılım Fonu", "Borçlanma Araçları Fonu", "Borçlanma Araçları Özel Fon",
        "Değişken Döviz Fon", "Değişken Fon", "Değişken Özel Fon", "Diğer Değişken Fon",
        "Endeks Hisse Senedi Fonu", "Eurobond Borçlanma Araçları Fonu", "Fon Sepeti Fonu",
        "Fon Sepeti Özel Fonu", "Fon Sepeti Serbest Fon", "Hisse Senedi Fonu",
        "Hisse Senedi Serbest Fon", "Hisse Senedi Serbest Özel Fon", "Karma Fon",
        "Katılım Döviz Fon", "Katılım Fonu", "Katılım Hisse Senedi Fonu",
        "Katılım Serbest Döviz Özel Fon", "Katılım Serbest Fon", "Katılım Serbest Özel Fon",
        "Kısa Vadeli Borçlanma Araçları Fonu", "Kısa Vadeli Katılım Serbest Fon",
        "Kısa Vadeli Kira Sertifikası Katılım", "Kısa Vadeli Serbest Fon",
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
        # URL'yi oluştur
        date_str = date.strftime("%Y%m%d")
        url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=F&type=F&fundType=99999&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
        
        try:
            # API'ye istek gönder
            response = requests.get(url, timeout=10)  # 10 saniye zaman aşımı
            response.raise_for_status()  # HTTP hatası varsa istisna fırlatır

            # Yanıtı kontrol et ve dosyayı oku
            if response.status_code == 200:
                df = pd.read_excel(BytesIO(response.content))

                # Kategorilerle eşleşen verileri filtrele
                df_filtered = df[df[df.columns[0]].isin(categories_of_interest)].set_index(df.columns[0])

                # İlgili veriyi sakla
                data[label] = df_filtered[df.columns[1]]
            else:
                st.error(f"API'den veri alınırken hata oluştu. Durum Kodu: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            # İstek sırasında oluşan hataları logla
            st.error(f"İstek sırasında hata oluştu: {e}")

    # Veriyi döndür
    return data

# --- Kullanıcıdan Tarih Seçimi ---
st.sidebar.header("Tarih Seçimi")
selected_date = st.sidebar.date_input("Tarih Seçin", datetime.today())

# --- Veriyi indir ve işle ---
data = load_data(selected_date)

# --------------------------
# Fon Akımları Grafiği
# --------------------------
st.sidebar.header("Fon Akımları Grafiği")
pysh_list = sorted(data.keys())  # pysh_list'i dinamik hale getirdim
selected_pysh = st.sidebar.selectbox("PYŞ Seçin", pysh_list)

# --------------------------
# 📊 Veri Hazırlığı
# --------------------------
pysh_df = data["t"]  # "t" verisini kullanarak verileri işlemeye başlıyoruz
total_flows = pysh_df.sum()

summary_df = pd.DataFrame({
    "Varlık Sınıfı": pysh_df.columns,
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
    title=f"{selected_pysh} - {selected_date} Net Fon Akımı (Toplam: {total_sum_mn:,.1f} mn TL)",
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
# 📊 Kümülatif Net Giriş Grafik
# --------------------------

df_filtered = data["t"]  # "t" verisini alıyoruz ve tarih filtresini yapıyoruz
daily = df_filtered.groupby("Tarih")[pysh_df.columns].sum().div(1_000_000).round(2)
daily["Toplam"] = daily.sum(axis=1).round(2)
daily["Kümülatif Giriş"] = daily["Toplam"].cumsum()

# Grafik oluştur
fig2 = px.line(
    daily,
    x=daily.index,
    y="Kümülatif Giriş",
    title=f"{selected_pysh} Kümülatif Net Giriş - {selected_date}",
    labels={"value": "Kümülatif Giriş (M TL)", "Tarih": "Tarih"}
)

fig2.update_layout(template="plotly_white", height=500)
st.plotly_chart(fig2, use_container_width=True)

# --------------------------
# Fon Türü Değişim Grafik
# --------------------------

categories_of_interest = [
    "Altın Fonu", "Altın Katılım Fonu", "Borçlanma Araçları Fonu", "Borçlanma Araçları Özel Fon",
    "Değişken Döviz Fon", "Değişken Fon", "Değişken Özel Fon", "Diğer Değişken Fon",
    "Endeks Hisse Senedi Fonu", "Eurobond Borçlanma Araçları Fonu", "Fon Sepeti Fonu",
    "Fon Sepeti Özel Fonu", "Fon Sepeti Serbest Fon", "Hisse Senedi Fonu",
    "Hisse Senedi Serbest Fon", "Hisse Senedi Serbest Özel Fon", "Karma Fon",
    "Katılım Döviz Fon", "Katılım Fonu", "Katılım Hisse Senedi Fonu",
    "Katılım Serbest Döviz Özel Fon", "Katılım Serbest Fon", "Katılım Serbest Özel Fon",
    "Kısa Vadeli Borçlanma Araçları Fonu", "Kısa Vadeli Katılım Serbest Fon",
    "Kısa Vadeli Kira Sertifikası Katılım", "Kısa Vadeli Serbest Fon",
    "Kira Sertifikası Katılım Fonu", "Orta Vadeli Borçlanma Araçları Fonu",
    "Özel Sektör Borçlanma Araçları Fonu", "Para Piyasası Fonu", "Para Piyasası Katılım Fonu",
    "Serbest Döviz Fon", "Serbest Döviz Özel Fon", "Serbest Fon", "Serbest Özel Fon",
    "Uzun Vadeli Borçlanma Araçları Fonu", "Yabancı Borçlanma Araçları Fonu",
    "Yabancı Fon Sepeti Fonu", "Yabancı Hisse Senedi Fonu"
]

# Takasbank Verisi - Fon Türü Değişim
key = "rT4AQ2R2lXyX-Ys9LzTkPbJ8szIKc4w1xwMbqV-1v9-LnLjLKETltBqStY7ldLOK0"
t_date = selected_date
dates = {
    "t": t_date,
    "t7": t_date - timedelta(days=7),
    "t28": t_date - timedelta(days=28)
}

# --- Excel dosyalarını indir ve oku ---
data = {}
for label, date in dates.items():
    date_str = date.strftime("%Y%m%d")
    url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=F&type=F&fundType=99999&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
    response = requests.get(url)
    df = pd.read_excel(BytesIO(response.content))
    df = df[df[df.columns[0]].isin(categories_of_interest)].set_index(df.columns[0])
    data[label] = df[df.columns[1]]

# --- Veriyi birleştir, yüzdelere çevir ve değişimi hesapla ---
df_combined = pd.concat(data.values(), axis=1)
df_combined.columns = data.keys()
df_combined.loc["TOPLAM"] = df_combined.sum()

df_percent = df_combined.drop("TOPLAM").div(df_combined.loc["TOPLAM"], axis=1)
df_percent["Haftalık Değ (bps)"] = (df_percent["t"] - df_percent["t7"]) * 10000
df_percent["Aylık Değ (bps)"] = (df_percent["t"] - df_percent["t28"]) * 10000
df_percent = df_percent.round(1)

# --- Grafik için veriler ---
plot_data = df_percent[["Haftalık Değ (bps)", "Aylık Değ (bps)"]].rename(columns={
    "Haftalık Değ (bps)": "Haftalık Değ",
    "Aylık Değ (bps)": "Aylık Değ"
})
t_amount_billion = df_combined.loc[sort_order, "t"] / 1e9

# --- Grafik çizimi ---
fig, ax1 = plt.subplots(figsize=(12, 10))
plot_data.plot(kind="barh", ax=ax1, width=0.6, color={
    "Haftalık Değ": "#162336",
    "Aylık Değ": "#cc171d"
})

ax1.set_title(f"Fon Türü Bazında Değişim {selected_date.strftime('%d %B %Y')} itibari ile (bps)", fontsize=16)
ax1.set_xlabel("Değişim (bps)", fontsize=13)
ax1.set_ylabel("Fon Türü", fontsize=14)
ax1.grid(axis="x", linestyle="--", alpha=0.6)
ax1.legend(loc="center right")
ax1.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f'))
ax1.invert_yaxis()

# --- Noktaları ve değer etiketlerini çiz ---
ax2 = ax1.twiny()
ax2.scatter(t_amount_billion.values, range(len(t_amount_billion)), color="royalblue", marker="o", label="Büyüklük (Milyar TL)")
ax2.set_xlabel("Büyüklük (Milyar TL)")
ax2.set_xlim(0, t_amount_billion.max() * 1.3)
ax2.set_yticks(range(len(t_amount_billion)))
ax2.set_yticklabels(df_percent.index.tolist())
ax2.legend(loc="upper left")

# Etiket ekle
for i, value in enumerate(t_amount_billion.values):
    label = f"{int(round(value)):,}".replace(",", ".")
    ax2.text(value * 1.10, i, label, va='center', fontsize=12, color="#355765",
             bbox=dict(boxstyle="round,pad=0.1", facecolor="#FFFFFF6F", edgecolor="none"))

st.pyplot(fig)
