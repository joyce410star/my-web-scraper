import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import urllib3
from urllib.parse import urljoin
import io
import zipfile

# 1. 基礎安全與介面設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="AI 全能數據偵察兵", page_icon="🚀", layout="wide")

# 自定義 CSS 讓介面更美觀
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 AI 全能數據偵察兵 v3.0")
st.write("一鍵掃描全球網頁：提取文字、分析關鍵字、抓取圖片並支援打包下載。")

# 2. 核心輸入區塊（移至中間最顯眼處）
with st.container():
    target_url = st.text_input("📍 請貼上目標網址 (URL):", "https://zh.wikipedia.org/wiki/網路爬蟲")
    col1, col2 = st.columns([1, 1])
    with col1:
        start_btn = st.button("🔥 啟動深度掃描")
    with col2:
        # 側邊欄改為滑動式參數調整
        st.write("") 

# 3. 側邊欄設定
with st.sidebar:
    st.header("🛠️ 偵察參數設定")
    min_word_len = st.slider("過濾最小字數", 2, 100, 10)
    top_n_images = st.slider("圖片預覽數量", 4, 40, 16)
    st.markdown("---")
    st.info("💡 提示：若遇到 'Just a moment' 頁面，代表該網站有強力防火牆。")

# 4. 爬蟲主邏輯
if start_btn:
    try:
        with st.spinner('🕵️ 正在執行多重偽裝並提取數據...'):
            # 強化的 Headers 偽裝
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/'
            }
            
            response = requests.get(target_url, headers=headers, verify=False, timeout=15)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')

            # --- A. 文字數據處理 ---
            raw_text_list = []
            full_content_for_cloud = ""
            for tag in ['h1', 'h2', 'h3', 'p', 'li']:
                for item in soup.find_all(tag):
                    text = item.get_text().strip()
                    if len(text) >= min_word_len:
                        raw_text_list.append(text)
                        full_content_for_cloud += text + " "
            
            df = pd.DataFrame(list(dict.fromkeys(raw_text_list)), columns=["內容"])

            # --- B. 圖片數據處理 ---
            img_links = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    img_links.append(urljoin(target_url, src))
            img_links = list(dict.fromkeys(img_links)) # 去重

            # --- 5. 數據呈現 (Tabs 介面) ---
            st.subheader("📊 掃描報告摘要")
            m1, m2, m3 = st.columns(3)
            m1.metric("文字段落", len(df))
            m2.metric("圖片總數", len(img_links))
            m3.metric("狀態碼", response.status_code)

            tab_text, tab_cloud, tab_img = st.tabs(["📄 文字情報", "☁️ 關鍵字雲分析", "🖼️ 多媒體牆"])

            with tab_text:
                search = st.text_input("🔍 關鍵字搜尋：")
                final_df = df[df['內容'].str.contains(search)] if search else df
                st.dataframe(final_df, use_container_width=True)
                
                csv_data = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 匯出 CSV 資料報表", csv_data, "report.csv", "text/csv")

            with tab_cloud:
                if len(full_content_for_cloud) > 20:
                    # 使用 jieba 進行中文分詞
                    words = jieba.lcut(full_content_for_cloud)
                    # 過濾掉單個字與空白
                    words_filtered = " ".join([w for w in words if len(w) > 1])
                    
                    # 生成詞雲
                    wc = WordCloud(
                        font_path=None, # Streamlit Cloud 預設字體
                        width=1000, height=500, 
                        background_color="white",
                        colormap='viridis'
                    ).generate(words_filtered)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)
                else:
                    st.warning("文字內容不足以生成分析圖表。")

            with tab_img:
                if img_links:
                    st.write(f"📸 正在顯示前 {top_n_images} 張圖片：")
                    
                    # 圖片 ZIP 打包下載功能
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for i, url in enumerate(img_links[:top_n_images]):
                            try:
                                img_res = requests.get(url, timeout=5)
                                if img_res.status_code == 200:
                                    zip_file.writestr(f"image_{i}.jpg", img_res.content)
                            except:
                                continue
                    
                    st.download_button("📦 打包下載所有圖片 (.zip)", zip_buffer.getvalue(), "images.zip", "application/zip")

                    # 圖片顯示
                    cols = st.columns(4)
                    for idx, url in enumerate(img_links[:top_n_images]):
                        with cols[idx % 4]:
                            st.image(url, use_container_width=True)
                else:
                    st.info("此網頁未偵測到圖片連結。")

    except Exception as e:
        st.error(f"⚠️ 偵察中斷：{e}")

st.markdown("---")
st.caption("🚀 AI Scraper Engine | Powered by Streamlit & Python 3.14")
