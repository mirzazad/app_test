import streamlit as st
import pandas as pd
import gdown

# Dosya ID'lerini ve URL'lerini ayarlıyoruz
main_df_url = "https://drive.google.com/uc?id=1NhD3-QLAvgOjfzrgMuyf-9Oeu_gHEOiA"  # Main dataframe linki
fund_info_url = "https://drive.google.com/uc?id=1e3OE8r7ZuYe5vvOKPR9_TjuMNyDdLx2r"  # Fund info linki

# Dosyaları indiriyoruz
def download_files():
    # Ana veri setini indir
    main_df_output = 'main_df.pkl'
    gdown.download(main_df_url, main_df_output, quiet=False)

    # Fund info dosyasını indir
    fund_info_output = 'fund_info.pkl'
    gdown.download(fund_info_url, fund_info_output, quiet=False)

    # Dosyaları pandas ile oku
    try:
        main_df = pd.read_pickle(main_df_output)
        fund_info = pd.read_pickle(fund_info_output)
        return main_df, fund_info
    except Exception as e:
        st.error(f"Error reading pickle file: {e}")
        return None, None

# Dosyaları indir ve oku
main_df, fund_info = download_files()

# Veriyi kontrol et
if main_df is not None and fund_info is not None:
    st.write("Ana veri seti (main_df) ve fon bilgileri (fund_info) başarıyla okundu.")
    st.write(main_df.head())  # Ana veriyi göster
    st.write(fund_info.head())  # Fon bilgilerini göster
else:
    st.warning("Veri okuma hatası!")
