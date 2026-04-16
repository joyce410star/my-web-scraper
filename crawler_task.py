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

# 1. 基礎設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="AI 數據偵察兵-暴力掃描版", page_icon="🕵️", layout="wide")

# 介面美化
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #ff4b4b; color: white; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 全能數據偵察兵 (暴力掃描模式)")
st.write("本版本擴大抓取範圍，確保不漏掉網頁上任何角落的文字與影像。")

# 2. 核心輸入區
with st.container():
    target_url = st.text_input("📍 請貼上目標網址 (URL):", "https://zh.wikipedia.org/wiki/網路爬蟲")
    start_btn = st.button("🚀 開始全方位執行掃描")

st.markdown("---")

# 3. 側邊欄：參數全開模式
with st.sidebar:
    st.header("⚙️ 偵察參數設定")
    # 預設調低到 2，這樣連短句都會抓到
    min_word_len = st.slider("過濾最小字數 (調低可抓更多)", 0, 50, 2)
    top_n_images = st.slider("圖片預覽數量", 4, 100, 20)
    st.markdown("---")
    st.write("✅ **目前模式：地毯式搜索**")
    st.write("已加入標籤：`h1-h3`, `p`, `li`, `div`, `span`")

# 4. 爬蟲主邏輯
if start_btn:
    try:
        with st.spinner('🕵️ 正在進行深度解析中...'):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = requests.get(target_url, headers=headers, verify=False, timeout=15)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')

            # --- 文字抓取：擴大範圍至所有常見標籤 ---
            raw_text_list = []
            full_text_content = ""
            # 這裡加入了 div 和 span，會抓到非常細碎的資料
            for tag in ['h1', 'h2', 'h3', 'p', 'li', 'div', 'span']:
                for item in soup.find_all(tag):
                    # 僅抓取直接子層文字，避免 div 巢狀重複抓取
                    text = item.get_text(strip=True)
                    if len(text) >= min_word_len:
                        raw_text_list.append(text)
                        full_text_content += text + " "
            
            # 移除完全重複的行
            unique_data = []
            for d in raw_text_list:
                if d not in unique_data:
                    unique_data.append(d)
            
            df = pd.DataFrame(unique_data, columns=["內容"])

            # --- 圖片抓取 ---
            img_links = [urljoin(target_url, img.get('src')) for img in soup.find_all('img') if img.get('src')]
            img_links = list(dict.fromkeys(img_links))

            # --- 數據呈現 ---
            st.subheader("📊 掃描報告摘要")
            m1, m2, m3 = st.columns(3)
            m1.metric("抓取總段落", len(unique_data))
            m2.metric("發現圖片數", len(img_links))
            m3.metric("連線狀態", response.status_code)

            tab_text, tab_cloud, tab_img = st.tabs(["📄 文字內容", "☁️ 關鍵字分析", "🖼️ 多媒體牆"])

            with tab_text:
                search = st.text_input("🔍 在結果中搜尋：")
                display_df = df[df['內容'].str.contains(search)] if search else df
                st.dataframe(display_df, use_container_width=True)
                st.download_button("📥 匯出 CSV", display_df.to_csv(index=False).encode('utf-8-sig'), "data.csv")

            with tab_cloud:
                if len(full_text_content) > 10:
                    words = jieba.lcut(full_text_content)
                    words_space = " ".join([w for w in words if len(w) > 1])
                    wc = WordCloud(width=1000, height=500, background_color="white").generate(words_space)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)
                else:
                    st.info("內容不足以生成分析。")

            with tab_img:
                if img_links:
                    # 圖片 ZIP 打包
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for i, url in enumerate(img_links[:top_n_images]):
                            try:
                                r = requests.get(url, timeout=5)
                                if r.status_code == 200:
                                    zip_file.writestr(f"img_{i}.jpg", r.content)
                            except: continue
                    st.download_button("📦 打包下載圖片 (.zip)", zip_buffer.getvalue(), "images.zip")

                    cols = st.columns(4)
                    for idx, url in enumerate(img_links[:top_n_images]):
                        with cols[idx % 4]:
                            st.image(url, use_container_width=True)
                else:
                    st.write("找不到圖片。")

    except Exception as e:
        st.error(f"掃描失敗：{e}")
