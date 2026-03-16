import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math

# ==========================================
# ⚙️ 網頁基本設定
# ==========================================
st.set_page_config(page_title="光茵築夢日記", page_icon="🏢", layout="wide")

# ==========================================
# 👑 1. 視覺與迎賓區 (標題與右上角計數器)
# ==========================================
col_title, col_counter = st.columns([3, 1])

with col_title:
    # 📝 調整 3：更改標題為光茵築夢日記
    st.title("🏢 光茵築夢日記")
    
with col_counter:
    st.write("") # 稍微往下推一點點來對齊標題
    
    # 🌟 採用驗證過的 hits.sh 穩定版計數器！
    # ⚠️ 記得把下面的 forworld-hills.streamlit.app 換成你剛剛真正部署成功的那個網址喔！
    st.markdown('''
    <div style='display: flex; justify-content: flex-end; align-items: center; font-size: 15px; color: #666666; font-weight: bold;'>
        <span style='margin-right: 8px;'>👁️ 芳鄰瀏覽：</span>
        <img src="https://hits.sh/forworld-hills.streamlit.app.svg?label=累計&color=79C83D&labelColor=555555" alt="views"/>
    </div>
    ''', unsafe_allow_html=True)
    
st.info("本系統由 B6-8F 芳鄰 (Jerry) 開發，自動連線抓取新北市政府建管系統數據，提供最新工程進度紀錄。")

# 換成你提供的建案渲染圖網址

# 註釋掉原本的 GitHub 網址
st.image("https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/header.jpg", 
         caption="建案周邊街景意象圖", use_container_width=True)


# 改為直接讀取同資料夾下的本地檔案
#st.image("header.jpg", caption="馥華之丘-光茵 完工意象圖", use_container_width=True)

# ==========================================
# 📥 2. 讀取 GitHub 雲端資料庫
# ==========================================
csv_url = "https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/history.csv"

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(csv_url)
        df['掛號日期'] = pd.to_datetime(df['掛號日期'])
        df = df.sort_values(by='掛號日期').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"連線失敗，請檢查 GitHub CSV 檔案。")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 🧠 3. 智慧交屋推估引擎 (含視覺化進度條與倒數修復)
# ==========================================
if not df.empty:
    today = datetime.now()
    
    # --- 關鍵數據提取 ---
    start_date = df['掛號日期'].min()
    days_since_start = (today - start_date).days
    
    all_roof_slabs = df[df['勘驗項目'].str.contains('頂版')]
    above_ground_slabs = df[df['勘驗項目'].str.contains('地上') & df['勘驗項目'].str.contains('頂版')]
    
    # --- 模型參數設定 ---
    TOTAL_FLOORS = 25           
    BUFFER_DAYS = 180           
    
    if len(above_ground_slabs) >= 2:
        duration = (above_ground_slabs['掛號日期'].max() - above_ground_slabs['掛號日期'].min()).days
        slabs_count = len(above_ground_slabs) - 1
        avg_days_per_floor = duration / slabs_count
    else:
        avg_days_per_floor = 28.3 

    # --- 剩餘時間與交屋日計算 (💡 修正倒數不變的 Bug) ---
    remaining_floors = TOTAL_FLOORS - len(all_roof_slabs)
    if remaining_floors < 0: remaining_floors = 0
        
    # 1. 抓出「最新一次」的工程進度日期當作起算錨點
    last_record_date = df['掛號日期'].max()
    
    # 2. 從「最新進度日」開始推算，還需要多少天
    days_needed_from_last = math.ceil(remaining_floors * avg_days_per_floor) + BUFFER_DAYS
    
    # 3. 算出絕對的「目標交屋日」
    target_date = last_record_date + timedelta(days=days_needed_from_last)
    
    # 4. 今天的剩餘天數 = 目標交屋日 - 今天 (這樣每天都會自動減 1 天！)
    days_to_delivery = (target_date - today).days
    if days_to_delivery < 0: days_to_delivery = 0
        
    target_month_str = f"程式動態推估預計 {target_date.year} 年 {target_date.month} 月交屋"
    
    # --- UI 儀表板顯示 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👷 已開工天數", f"{days_since_start} 天", help=f"開工日期：{start_date.strftime('%Y-%m-%d')}")
    with col2:
        st.metric("🏗️ 地上層平均工期", f"{avg_days_per_floor:.1f} 天/層")
    with col3:
        # 加一個向下的紅色小箭頭，讓大家感覺天數在變少
        st.metric("⏳ 預估交屋剩餘天數", f"{days_to_delivery} 天", f"-1 天 (每日遞減)", delta_color="inverse")
        
    # --- 🌟 提案 A：建築主體工程視覺化進度條 (地上層精準版) ---
    st.markdown("<br>", unsafe_allow_html=True) # 加一點空白讓版面呼吸
    
    # 修正：只計算「地上層」的進度百分比，對齊總樓層 25 樓
    completed_above_floors = len(above_ground_slabs)
    progress_ratio = completed_above_floors / TOTAL_FLOORS
    if progress_ratio > 1.0: progress_ratio = 1.0 
    progress_percent = int(progress_ratio * 100)
    
    # 計算地下室蓋了幾層 (總頂版數 - 地上頂版數)
    underground_slabs = len(all_roof_slabs) - completed_above_floors

    # 顯示文字與進度條
    st.write(f"**🏢 地上主體結構進度：** 目前已蓋至 **地上 {completed_above_floors} 層** / 總計 {TOTAL_FLOORS} 層 **({progress_percent}%)**")
    st.progress(progress_ratio) # 繪製 Streamlit 內建綠色進度條
    
    # 排版巧思：左邊放地下室備註，右邊放交屋年月
    col_sub1, col_sub2 = st.columns([1, 1])
    with col_sub1:
        if underground_slabs > 0:
            st.markdown(f"<div style='color: #888888; font-size: 13px;'>*(註：已完成 {underground_slabs} 層地下室結構)*</div>", unsafe_allow_html=True)
    with col_sub2:
        st.markdown(f"<div style='text-align: right; color: gray; font-size: 14px; font-weight: bold;'>{target_month_str}</div>", unsafe_allow_html=True)

    # 📝 免責聲明
    st.caption("⚠️ **預估時程免責聲明**：以上預估交屋天數與日期，係由系統依據目前「地上層」實際過件進度動態推算，僅供芳鄰參考。**不保證實際完工日期，確切交屋時程請以馥華集團正式公告為準。**")

    st.markdown("---")
    
# ==========================================
    # 📸 4. 施工紀錄與相簿派發中心
    # ==========================================
    st.subheader("📜 工程進度施工紀錄與實況")

    # 🌟 宏信專屬：單一總相簿設計！(只要設定一次，以後都不用改程式碼)
    MASTER_ALBUM_URL = "https://drive.google.com/drive/folders/1jgaPFGbTZS707tToVchHkqN5Xuu7gJ98?usp=sharing"
    
    # 在時間軸最上方放一個非常顯眼的總相簿大按鈕
    st.info("💡 想要看更完整的施工細節與歷程嗎？")
    st.link_button("☁️ 前往 Google Drive 查看【光茵築夢全紀錄】總相簿", MASTER_ALBUM_URL, use_container_width=True)
    st.markdown("---")

    # 🖼️ 【精選輪播照片區】: 放 1~3 張最精華的照片，網頁直接顯示
    MILESTONE_PHOTOS = {
        "地上4樓頂版勘驗": [
            {"url": "https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/photos/4f_1.jpg", "tab_name": "📸 AB棟空拍 (一)", "caption": "工地空拍照 1"},
            {"url": "https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/photos/4f_2.jpg", "tab_name": "📸 AB棟空拍 (二)", "caption": "工地空拍照 2"},
            {"url": "https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/photos/4f_3.jpg", "tab_name": "📸 金城交流道", "caption": "空拍照"}
        ],
        "開工報告-": [
            {"url": "https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/photos/start_1.jpg", "tab_name": "📸 動土典禮-致詞", "caption": "馥華之丘-光茵 盛大開工"},
            {"url": "https://raw.githubusercontent.com/Jerry7135/forworld-hills-tracker/main/photos/start_2.jpg", "tab_name": "📸 動土典禮-祈福", "caption": "馥華之丘-光茵 盛大開工"}
        ]
    }
    
    # ... (上面保留你原本的 MASTER_ALBUM_URL 總相簿大按鈕 與 MILESTONE_PHOTOS 字典) ...

    # 🌟 提案 D：歷史紀錄一鍵篩選器
    st.markdown("##### 🔍 快速篩選工程階段")
    filter_option = st.radio(
        "請選擇你想查看的進度範圍：",
        ["🏢 全部顯示", "🌥️ 只看地上層", "🕳️ 只看地下室與基礎"],
        horizontal=True, # 讓按鈕橫向排列，節省空間
        label_visibility="collapsed" # 隱藏標題讓版面更簡潔
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # 確保由新到舊排序
    latest_df = df.sort_values(by='掛號日期', ascending=False).reset_index(drop=True)
    
    # 🧠 根據使用者的選擇，動態過濾資料表
    if filter_option == "🌥️ 只看地上層":
        latest_df = latest_df[latest_df['勘驗項目'].str.contains('地上')]
    elif filter_option == "🕳️ 只看地下室與基礎":
        # 地下室階段的名稱可能包含「地下」、「基礎」、「支撐」或「開挖」，用 | (OR) 來聯集
        latest_df = latest_df[latest_df['勘驗項目'].str.contains('地下|基礎|支撐|開挖|擋土')]

    # 重新發放 index (讓最新的那一筆依然可以是 index 0，預設展開)
    latest_df = latest_df.reset_index(drop=True)

    # 接下來就是你原本的迴圈，把 latest_df 畫出來
    for index, row in latest_df.iterrows():
        is_latest = (index == 0)
        
        # ... (以下維持你原本的 with st.expander... 程式碼不動) ...
        
        with st.expander(f"{title_prefix}{row['掛號日期'].strftime('%Y-%m-%d')} - {row['勘驗項目']}", expanded=is_latest):
            
            if is_latest:
                st.success("✨ 這是目前光茵最新的工程進度！")
                
            c1, c2 = st.columns([1, 1.8]) # 調整左右比例，讓照片大一點
            with c1:
                st.write(f"**審核進度：** `{row['審核進度']}`")
                st.write(f"**掛號號碼：** `{row['掛號號碼']}`")

            with c2:
                milestone_name = row['勘驗項目']
                
                # 檢查這層樓有沒有設定精選照片
                if milestone_name in MILESTONE_PHOTOS and len(MILESTONE_PHOTOS[milestone_name]) > 0:
                    photos = MILESTONE_PHOTOS[milestone_name]
                    
                    # 建立分頁 (Tabs) 來達成輪播效果
                    tab_names = [p["tab_name"] for p in photos]
                    tabs = st.tabs(tab_names)
                    
                    # 依序把照片塞進對應的分頁裡
                    for i, tab in enumerate(tabs):
                        with tab:
                            st.image(photos[i]["url"], caption=photos[i]["caption"], use_container_width=True)
                else:
                    # 如果沒有設定相片，就顯示一張極簡的暫存圖，保持版面整齊
                    st.image("https://via.placeholder.com/800x400.png?text=Forworld+Hills+Construction", 
                             caption=f"{milestone_name} (暫無精選相片)", use_container_width=True)

else:
    st.warning("⚠️ 儀表板連線中，請確認 GitHub 專案中的 history.csv 是否存在。")
