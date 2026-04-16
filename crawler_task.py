import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import urllib3
from urllib.parse import urljoin, urlparse
import io
import zipfile
import re
import time
from collections import Counter

# --- 1. 核心環境設定 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="AI 究極情資分析系統",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入高級 CSS 樣式
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 12px; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background: linear-gradient(45deg, #1f4037, #99f2c8); 
        color: white; font-weight: bold; border: none;
    }
    .metric-card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 輔助函式庫 ---
def get_safe_filename(url):
    return re.sub(r'[\\/*?:"<>|]', "", urlparse(url).netloc)

def extract_keywords(text, top_k=20):
    words = jieba.lcut(text)
    # 過濾掉單字、符號與空白
    stop_words = ['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這']
    filtered = [w for w in words if len(w) > 1 and w not in stop_words and not w.isspace()]
    return Counter(filtered).most_common(top_k)

# --- 3. 側邊欄：深度設定 ---
with st.sidebar:
    st.header("🛠️ 深度搜索配置")
    st.info("本系統採地毯式搜索，將挖掘 HTML 每一層標籤。")
    
    with st.expander("📝 文字採集設定", expanded=True):
        min_len = st.number_input("最小字數過濾", 0, 100, 0)
        include_div = st.checkbox("包含 <div> 與 <span> (增加細節)", True)
        include_links = st.checkbox("包含 <a> 連結文字", True)
    
    with st.expander("🖼️ 影像採集設定", expanded=True):
        img_limit = st.slider("最大抓取張數", 10, 500, 100)
        check_lazy_load = st.checkbox("深度挖掘懶加載屬性", True)
    
    st.markdown("---")
    st.caption("Engine: Python 3.14 Professional Edition")

# --- 4. 主介面佈局 ---
st.title("📡 AI 究極情資分析系統 v5.0")
st.caption("地毯式掃描、深度自然語言處理 (NLP)、多媒體打包。")

input_col, btn_col = st.columns([4, 1])
with input_col:
    url = st.text_input("📍 請輸入全球監控目標 (URL):", "https://zh.wikipedia.org/wiki/網路爬蟲")
with btn_col:
    st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    start_run = st.button("🚀 啟動全方位掃描")

# --- 5. 執行核心 ---
if start_run:
    if not url.startswith("http"):
        st.error("❌ 請輸入完整的網址 (需包含 http:// 或 https://)")
    else:
        try:
            start_time = time.time()
            progress_bar = st.progress(0)
            
            # 5.1 偽裝請求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache'
            }
            
            progress_bar.progress(20, text="正在穿透防火牆並下載原始碼...")
            res = requests.get(url, headers=headers, verify=False, timeout=20)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')

            # 5.2 暴力提取文字
            progress_bar.progress(40, text="正在執行地毯式文字提取...")
            target_tags = ['h1', 'h2', 'h3', 'h4', 'p', 'li']
            if include_div: target_tags.extend(['div', 'span'])
            if include_links: target_tags.append('a')
            
            raw_text = []
            for tag in target_tags:
                for item in soup.find_all(tag, recursive=True):
                    # 抓取直接文字，避免巢狀結構造成嚴重重複
                    t = item.get_text(strip=True)
                    if len(t) >= min_len:
                        raw_text.append(t)
            
            # 數據清理：去重、去空
            unique_text = []
            [unique_text.append(x) for x in raw_text if x not in unique_text]
            full_corpus = " ".join(unique_text)

            # 5.3 深度提取影像
            progress_bar.progress(60, text="正在挖掘隱藏多媒體資源...")
            all_imgs = []
            img_attrs = ['src', 'data-src', 'data-original', 'srcset', 'original', 'file'] if check_lazy_load else ['src']
            
            for img in soup.find_all('img'):
                for attr in img_attrs:
                    src = img.get(attr)
                    if src:
                        # 處理 srcset 內可能包含多個網址的情況
                        actual_src = src.split(' ')[0]
                        img_url = urljoin(url, actual_src)
                        if img_url.startswith('http'):
                            all_imgs.append(img_url)
            
            all_imgs = list(dict.fromkeys(all_imgs))[:img_limit]

            # 5.4 計算與視覺化
            progress_bar.progress(90, text="正在生成 AI 分析報告...")
            keywords = extract_keywords(full_corpus)
            
            # --- 6. 視覺化報告呈現 ---
            progress_bar.empty()
            st.success(f"✅ 掃描完成！耗時: {round(time.time() - start_time, 2)}s")

            # A. 指標區
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("採集文字段落", len(unique_text))
            m2.metric("挖掘影像資源", len(all_imgs))
            m3.metric("網頁總字數", len(full_corpus))
            m4.metric("HTTP 狀態", res.status_code)

            # B. 分頁系統
            tab1, tab2, tab3, tab4 = st.tabs(["📄 數據明細", "🧠 NLP 分析", "🖼️ 多媒體牆", "🛠️ 系統日誌"])

            with tab1:
                st.subheader("原始數據清單")
                df = pd.DataFrame(unique_text, columns=["抓取內容"])
                st.dataframe(df, use_container_width=True, height=500)
                
                c1, c2 = st.columns(2)
                c1.download_button("📥 匯出 CSV 報表", df.to_csv(index=False).encode('utf-8-sig'), "data_export.csv", "text/csv")
                c2.download_button("📥 匯出 Excel (JSON)", df.to_json().encode('utf-8'), "data_export.json", "application/json")

            with tab2:
                col_left, col_right = st.columns([1, 1])
                with col_left:
                    st.subheader("💡 關鍵詞頻率統計")
                    if keywords:
                        key_df = pd.DataFrame(keywords, columns=["關鍵字", "頻率"])
                        st.bar_chart(key_df.set_index("關鍵字"))
                with col_right:
                    st.subheader("☁️ AI 詞雲圖")
                    if len(full_corpus) > 20:
                        wc = WordCloud(font_path=None, width=800, height=600, background_color="white", colormap="magma").generate(" ".join(jieba.lcut(full_corpus)))
                        fig, ax = plt.subplots()
                        ax.imshow(wc, interpolation='bilinear'); ax.axis("off")
                        st.pyplot(fig)

            with tab3:
                if all_imgs:
                    st.subheader(f"影像採集結果 ({len(all_imgs)})")
                    # 批量下載功能
                    zip_io = io.BytesIO()
                    with zipfile.ZipFile(zip_io, "w") as zf:
                        for idx, img_url in enumerate(all_imgs):
                            try:
                                img_data = requests.get(img_url, timeout=5).content
                                zf.writestr(f"resource_{idx}.jpg", img_data)
                            except: continue
                    st.download_button("📦 打包所有影像 (.zip)", zip_io.getvalue(), "media_pack.zip")
                    
                    # 顯示牆
                    img_cols = st.columns(4)
                    for idx, img_url in enumerate(all_imgs):
                        with img_cols[idx % 4]:
                            st.image(img_url, use_container_width=True, caption=f"ID: {idx}")
                else:
                    st.warning("此目標網頁未發現影像資源。")

            with tab4:
                st.subheader("技術情資")
                st.json({
                    "Target URL": url,
                    "Headers": headers,
                    "Encoding": res.encoding,
                    "Content Type": res.headers.get('Content-Type'),
                    "Unique Tags Found": list(set([tag.name for tag in soup.find_all()]))
                })

        except Exception as e:
            st.error(f"❌ 系統發生嚴重錯誤: {str(e)}")

st.markdown("---")
st.caption("AI Ultimate Scraper v5.0 | 🛡️ 本工具僅限於合法公開數據採集使用")
