def show_fon_turu_chart(t_date: datetime):
    import plotly.graph_objects as go
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
    df_percent["Haftalık"] = (df_percent["t"] - df_percent["t7"]) * 10000
    df_percent["Aylık"] = (df_percent["t"] - df_percent["t28"]) * 10000
    df_percent = df_percent.round(1)

    sort_order = df_combined.drop("TOPLAM")["t"].sort_values(ascending=False).index
    df_percent = df_percent.loc[sort_order].reset_index().rename(columns={"index": "Fon Türü"})
    df_percent["Büyüklük (mlr TL)"] = df_combined.loc[sort_order, "t"].div(1e9).round(1).values

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_percent["Haftalık"],
        y=df_percent["Fon Türü"],
        name="Haftalık Değişim (bps)",
        orientation="h",
        marker_color="#162336"
    ))

    fig.add_trace(go.Bar(
        x=df_percent["Aylık"],
        y=df_percent["Fon Türü"],
        name="Aylık Değişim (bps)",
        orientation="h",
        marker_color="#cc171d"
    ))

    fig.add_trace(go.Scatter(
        x=df_percent["Büyüklük (mlr TL)"],
        y=df_percent["Fon Türü"],
        mode="markers",
        name="Büyüklük (mlr TL)",
        marker=dict(size=10, color="darkorange", symbol="circle"),
        hovertemplate='<b>%{y}</b><br>Büyüklük: %{x:,.1f} mlr TL',
        xaxis="x2",
        showlegend=True
    ))

    fig.update_layout(
        title=f"📅 {t_date.strftime('%d %B %Y')} – Fon Türü Bazında Değişim ve Büyüklük",
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
        yaxis=dict(title="Fon Türü"),
        legend=dict(orientation="h", y=-0.2),
        height=800,
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff",
        font=dict(size=13, family="Segoe UI")
    )

    st.plotly_chart(fig, use_container_width=True, key="fon_turu_chart")
