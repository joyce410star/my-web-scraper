import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
from urllib.parse import urljoin

# 基礎設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="專業級情資分析爬蟲", page_icon="🕵️", layout="wide")

# --- 主標題區 ---
st.title("🕵️ 專業級網頁情資分析系統")
st.write("請在下方輸入網址，系統將自動掃描文字、圖片並進行數據分析。")

# --- 【關鍵修改】將輸入框移到正中間 ---
# 使用 st.container 讓它看起來更像一個獨立的搜尋區塊
with st.container():
    # 使用 columns 讓輸入框和按鈕排在同一行，或上下緊鄰
    target_url = st.text_input("📍 請貼上目標網址 (URL):", "https://zh.wikipedia.org/wiki/網路爬蟲", help="請確保包含 http 或 https")
    col_btn, _ = st.columns([1, 4]) # 讓按鈕不要太寬
    start_button = col_btn.button("🚀 開始全方位執行掃描", use_container_width=True)

st.markdown("---")

# --- 側邊欄：僅保留微調參數 ---
with st.sidebar:
    st.header("⚙️ 篩選參數設定")
    min_length = st.slider("過濾最小字數:", 0, 100, 10)
    show_images = st.checkbox("抓取並顯示圖片", value=True)
    st.info("提示：增加最小字數可以過濾導覽列雜訊。")

# --- 主程式邏輯 ---
if start_button:
    try:
        with st.spinner('正在掃描網頁內容，請稍候...'):
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
            response = requests.get(target_url, headers=headers, verify=False, timeout=15)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. 抓取文字內容
            tags = ['h1', 'h2', 'h3', 'p', 'li', 'div']
            raw_data = []
            for tag in tags:
                for item in soup.find_all(tag):
                    text = item.get_text().strip()
                    if text and len(text) >= min_length:
                        raw_data.append(text)
            
            unique_data = list(dict.fromkeys(raw_data))
            df = pd.DataFrame(unique_data, columns=["內容"])

            # 2. 抓取圖片內容
            img_urls = []
            if show_images:
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src:
                        img_urls.append(urljoin(target_url, src))

            # --- 畫面呈現 ---
            # A. 數據指標區
            st.subheader("📊 數據摘要")
            c1, c2, c3 = st.columns(3)
            c1.metric("抓取總段落", len(unique_data))
            c2.metric("發現圖片數", len(img_urls))
            c3.metric("網頁標題", soup.title.string[:20] if soup.title else "無標題")

            # B. 分頁顯示結果
            tab1, tab2, tab3 = st.tabs(["📄 文字內容", "🖼️ 圖片牆", "📈 分佈分析"])
            
            with tab1:
                search = st.text_input("🔍 在結果中搜尋關鍵字:")
                display_df = df[df['內容'].str.contains(search)] if search else df
                st.dataframe(display_df, use_container_width=True)
                
                csv = display_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載篩選後的資料 (CSV)", csv, "scraped_data.csv", "text/csv")

            with tab2:
                if img_urls:
                    st.write(f"發現 {len(img_urls)} 張圖片（預覽前 16 張）：")
                    cols = st.columns(4)
                    for idx, url in enumerate(img_urls[:16]):
                        with cols[idx % 4]:
                            try:
                                st.image(url, use_container_width=True)
                            except:
                                pass
                else:
                    st.write("未發現可顯示的圖片。")

            with tab3:
                st.write("段落字數長度分佈（視覺化）：")
                df['字數'] = df['內容'].str.len()
                st.bar_chart(df['字數'])

    except Exception as e:
        st.error(f"掃描失敗，請確認網址是否正確：{e}")

st.markdown("---")
st.caption("Status: Python 3.14 Engine Running | Streamlit Interface v2.1")