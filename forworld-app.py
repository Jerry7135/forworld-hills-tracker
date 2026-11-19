import html
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import altair as alt
import pandas as pd
import streamlit as st

# ==========================================
# ⚙️ 設定區：換 GitHub 專案或調整內容，只要改這裡
# ==========================================
GITHUB_USER = "Jerry7135"
GITHUB_REPO = "forworld-hills-tracker"      # 👉 新測試專案請改成新的 repo 名稱
GITHUB_BRANCH = "main"

SITE_TITLE = "光茵築夢日記"
PROJECT_NAME = "馥華之丘-光茵"
AUTHOR_NOTE = "本站由 B6-8F 芳鄰 (Jerry) 開發維護"

TOTAL_FLOORS = 25          # 地上總樓層
BASEMENT_FLOORS = 4        # 地下樓層數
FALLBACK_START_DATE = datetime(2023, 9, 1)   # 找不到「開工報告」時的開工日

MASTER_ALBUM_URL = "https://drive.google.com/drive/folders/1jgaPFGbTZS707tToVchHkqN5Xuu7gJ98?usp=sharing"
LINE_ADD_FRIEND_URL = ""   # 👉 填入 LINE 官方帳號「加好友」連結 (例如 https://lin.ee/xxxx)，留空就不顯示按鈕
COUNTER_KEY = "forworld-hills.streamlit.app"  # 瀏覽計數器的名稱，維持不變就會接續原本的累計數

# 是否顯示「地上結構體」的參考完成月份 (只推估結構體，不推估交屋)
SHOW_STRUCTURE_ESTIMATE = True

# 照片是否透過 images.weserv.nl 自動縮圖 (大幅加快手機載入)；若圖片出不來可改成 False
USE_IMAGE_PROXY = True

# 結構體之後的階段：建管勘驗資料抓不到，請手動更新狀態
#   status 可填："todo" (尚未開始) / "doing" (進行中) / "done" (已完成)
#   note 可填任意文字，例如 "2027-03 開始"，留空就不顯示
LATER_STAGES = [
    {"name": "外牆磁磚",     "status": "todo", "note": ""},
    {"name": "內裝與機電",   "status": "todo", "note": ""},
    {"name": "拆除鷹架",     "status": "todo", "note": ""},
    {"name": "取得使用執照", "status": "todo", "note": ""},
    {"name": "交屋",         "status": "todo", "note": ""},
]

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
TW_TZ = timezone(timedelta(hours=8))

# ==========================================
# 🎨 網頁基本設定與樣式
# ==========================================
st.set_page_config(page_title=SITE_TITLE, page_icon="🏢", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1100px;}
.hero {position: relative; border-radius: 16px; overflow: hidden; min-height: 220px;
       background-size: cover; background-position: center; display: flex; align-items: flex-end;}
.hero-inner {width: 100%; padding: 22px 24px; color: #fff;
             background: linear-gradient(to top, rgba(0,0,0,.72), rgba(0,0,0,.05));}
.hero h1 {color: #fff !important; font-size: 2.1rem; margin: 0; padding: 0;}
.hero p {color: #eef5ea; margin: 4px 0 0 0; font-size: .95rem;}
.hero p.hero-note {display: inline-block; margin-top: 8px; padding: 2px 10px; border-radius: 999px;
                   background: rgba(255,255,255,.18); font-size: .8rem; color: #fff;}
.card {background: #fff; color: #1F2A1F; border: 1px solid #E3E9DF; border-radius: 14px; padding: 16px 18px;}
.latest {border-left: 6px solid #5FA82E; margin: 16px 0;}
.latest .label {font-size: .8rem; color: #5FA82E; font-weight: 700; letter-spacing: .05em;}
.latest .title {font-size: 1.3rem; font-weight: 700; margin: 2px 0 6px 0;}
.muted {color: #6B7768; font-size: .85rem;}
.kpis {display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 8px 0 18px 0;}
.kpi .k-label {font-size: .82rem; color: #6B7768;}
.kpi .k-value {font-size: 1.6rem; font-weight: 700; color: #1F2A1F; line-height: 1.3;}
.kpi .k-sub {font-size: .78rem; color: #8A9587;}
.badge {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .78rem; font-weight: 600;}
.b-ok {background: #E4F4DA; color: #2F6B12;} .b-wait {background: #FFF1D6; color: #8A5A00;}
.b-bad {background: #FDE2E1; color: #A3231C;} .b-other {background: #ECEFEA; color: #4A5547;}
.roadmap {list-style: none; padding: 0; margin: 0;}
.roadmap li {display: flex; gap: 12px; padding: 9px 0; border-bottom: 1px dashed #E3E9DF;}
.roadmap li:last-child {border-bottom: none;}
.roadmap .dot {flex: 0 0 26px; height: 26px; border-radius: 50%; display: flex; align-items: center;
               justify-content: center; font-size: .8rem; font-weight: 700;}
.dot-done {background: #5FA82E; color: #fff;} .dot-doing {background: #FFB020; color: #fff;}
.dot-todo {background: #ECEFEA; color: #8A9587;}
.roadmap .r-name {font-weight: 600;} .roadmap .r-note {font-size: .8rem; color: #6B7768;}
.bar {height: 8px; background: #ECEFEA; border-radius: 99px; margin-top: 5px; overflow: hidden; max-width: 220px;}
.bar > div {height: 100%; background: #5FA82E; border-radius: 99px;}
.year {font-size: 1.1rem; font-weight: 700; color: #5FA82E; margin: 22px 0 8px 0;}
.tl {display: flex; gap: 14px; margin-bottom: 12px;}
.tl .date {flex: 0 0 78px; text-align: right; font-weight: 700; color: #1F2A1F; padding-top: 16px; font-size: .9rem;}
.tl .date span {display: block; font-weight: 400; color: #8A9587; font-size: .75rem;}
.tl .card {flex: 1; min-width: 0;}
.tl .t-title {font-weight: 700; font-size: 1.05rem; margin-bottom: 4px;}
.tl.is-latest .card {border: 2px solid #5FA82E;}
.strip {display: flex; gap: 8px; overflow-x: auto; margin-top: 10px; padding-bottom: 4px;}
.strip a {flex: 0 0 auto;}
.strip img {height: 120px; width: auto; border-radius: 10px; display: block; background: #ECEFEA;}
.gallery {display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px; margin-bottom: 10px;}
.gallery figure {margin: 0; background: #fff; border: 1px solid #E3E9DF; border-radius: 12px; overflow: hidden;}
.gallery img {width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block; background: #ECEFEA;}
.gallery figcaption {padding: 8px 10px; font-size: .82rem; color: #4A5547;}
.gallery figcaption b {display: block; color: #1F2A1F; font-size: .88rem;}
.btn {display: inline-block; padding: 10px 18px; border-radius: 10px; font-weight: 600; text-decoration: none !important;}
.btn-line {background: #06C755; color: #fff !important;}
@media (max-width: 640px) {
  .hero {min-height: 170px;} .hero h1 {font-size: 1.6rem;}
  .kpis {grid-template-columns: repeat(2, 1fr);}
  .kpi .k-value {font-size: 1.3rem;}
  .tl {gap: 8px;} .tl .date {flex-basis: 56px; font-size: .8rem;}
  .strip img {height: 96px;}
}
</style>
""", unsafe_allow_html=True)


def show_html(s):
    """把 HTML 壓成無縮排的字串再輸出 (避免 Markdown 把縮排當成程式碼區塊)"""
    st.markdown("".join(line.strip() for line in s.splitlines()), unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x))


def photo_url(filename):
    return f"{RAW_BASE}/photos/{quote(str(filename))}"


def img_src(url, width):
    """縮圖網址：透過 images.weserv.nl 依寬度縮小，原圖仍保留在 GitHub"""
    if not USE_IMAGE_PROXY:
        return url
    return f"https://images.weserv.nl/?url={quote(url.replace('https://', ''), safe='')}&w={width}&q=72&output=jpg"


def badge(status):
    s = str(status)
    if "同意" in s or "准予" in s or "核准" in s:
        cls = "b-ok"
    elif "待審" in s or "審查" in s or "處理" in s:
        cls = "b-wait"
    elif "退" in s or "不" in s:
        cls = "b-bad"
    else:
        cls = "b-other"
    return f"<span class='badge {cls}'>{esc(s)}</span>"


def display_item(item):
    item = str(item).strip()
    if item in ("", "-", "nan"):
        return "新勘驗申請（審查中，項目尚未公布）"
    return item.rstrip("-").strip() or item


def parse_floor(item):
    """地下N樓 -> -N，地上N樓 -> N"""
    m = re.search(r'地下(\d+)樓', str(item))
    if m:
        return -int(m.group(1))
    m = re.search(r'地上(\d+)樓', str(item))
    if m:
        return int(m.group(1))
    return None


# ==========================================
# 📥 讀取資料 (GitHub 優先，失敗改讀同資料夾的檔案)
# ==========================================
def read_csv_any_encoding(src):
    """先用 UTF-8 讀；若檔案被 Excel 存成 Big5 (cp950) 也能讀"""
    last_err = None
    for enc in ("utf-8-sig", "cp950"):
        try:
            return pd.read_csv(src, dtype=str, encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
    raise last_err


def read_csv_remote_first(name):
    try:
        return read_csv_any_encoding(f"{RAW_BASE}/{quote(name)}")
    except Exception:
        return read_csv_any_encoding(name)


@st.cache_data(ttl=600)
def load_history():
    df = read_csv_remote_first("history.csv")
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    df['掛號日期'] = pd.to_datetime(df['掛號日期'])
    df['樓層'] = df['勘驗項目'].apply(parse_floor)
    return df.sort_values(by='掛號日期').reset_index(drop=True)


@st.cache_data(ttl=600)
def load_photos():
    try:
        p = read_csv_remote_first("photos.csv").fillna("")
        p.columns = [c.strip().lstrip("﻿") for c in p.columns]
        return p
    except Exception:
        return pd.DataFrame(columns=["勘驗項目", "檔名", "標題", "說明"])


try:
    df = load_history()
except Exception:
    df = pd.DataFrame()
photos = load_photos()

if df.empty:
    st.warning("⚠️ 目前讀不到工程進度資料，請稍後再試。")
    st.stop()

# ==========================================
# 🧮 計算進度 (只用建管處已有的勘驗資料，不推估交屋)
# ==========================================
today = datetime.now(TW_TZ).replace(tzinfo=None)

start_record = df[df['勘驗項目'].str.contains('開工報告', na=False)]
start_date = start_record['掛號日期'].iloc[0] if not start_record.empty else FALLBACK_START_DATE
days_since_start = (today - start_date).days

slabs = df[df['勘驗項目'].str.contains('頂版', na=False) & df['樓層'].notna()]
above = slabs[slabs['樓層'] > 0].sort_values('掛號日期')
below = slabs[slabs['樓層'] < 0]

current_floor = int(above['樓層'].max()) if not above.empty else 0
basement_done = int(-below['樓層'].min()) if not below.empty else 0
progress_ratio = min(current_floor / TOTAL_FLOORS, 1.0)

# 近期施工節奏：取最近 5 次地上頂版勘驗
pace = None
recent = above.tail(5)
if len(recent) >= 2:
    floors_diff = recent['樓層'].iloc[-1] - recent['樓層'].iloc[0]
    days_diff = (recent['掛號日期'].iloc[-1] - recent['掛號日期'].iloc[0]).days
    if floors_diff > 0:
        pace = days_diff / floors_diff

structure_estimate = None
if SHOW_STRUCTURE_ESTIMATE and pace and 0 < current_floor < TOTAL_FLOORS:
    remaining = TOTAL_FLOORS - current_floor
    last_slab_date = above['掛號日期'].max()
    early = last_slab_date + timedelta(days=remaining * pace * 0.9)
    late = last_slab_date + timedelta(days=remaining * pace * 1.3)
    if early.year == late.year:
        structure_estimate = f"{early.year} 年 {early.month}～{late.month} 月" if early.month != late.month else f"{early.year} 年 {early.month} 月"
    else:
        structure_estimate = f"{early.year} 年 {early.month} 月～{late.year} 年 {late.month} 月"

latest = df.iloc[-1]
days_ago = (today - latest['掛號日期']).days
days_ago_text = "今天" if days_ago <= 0 else f"{days_ago} 天前"

# ==========================================
# 👑 頁首
# ==========================================
show_html(f"""
<div class="hero" style="background-image:url('{img_src(f"{RAW_BASE}/header.jpg", 1600)}');">
  <div class="hero-inner">
    <h1>🏢 {esc(SITE_TITLE)}</h1>
    <p>{esc(PROJECT_NAME)}｜工程進度紀錄・資料來源：新北市政府工務局建管系統</p>
    <p class="hero-note">🏠 芳鄰自發製作的非官方紀錄站，與建商無關</p>
  </div>
</div>
<div class="card latest">
  <div class="label">最新進度・{esc(days_ago_text)}</div>
  <div class="title">{esc(display_item(latest['勘驗項目']))}</div>
  <div>{badge(latest['審核進度'])} <span class="muted">　掛號日期 {latest['掛號日期']:%Y-%m-%d}</span></div>
</div>
""")

tab_overview, tab_records, tab_album, tab_about = st.tabs(["📊 進度總覽", "📜 施工紀錄", "📸 相簿", "ℹ️ 關於本站"])

# ==========================================
# 📊 分頁一：進度總覽
# ==========================================
with tab_overview:
    pace_text = f"{pace:.0f}" if pace else "—"
    show_html(f"""
    <div class="kpis">
      <div class="card kpi"><div class="k-label">🏗️ 地上結構</div>
        <div class="k-value">{current_floor}F <span style="font-size:1rem;color:#8A9587;">/ {TOTAL_FLOORS}F</span></div>
        <div class="k-sub">完成 {progress_ratio:.0%}</div></div>
      <div class="card kpi"><div class="k-label">⏱️ 近期節奏</div>
        <div class="k-value">{pace_text} <span style="font-size:1rem;color:#8A9587;">天/層</span></div>
        <div class="k-sub">最近 {len(recent)} 次頂版勘驗</div></div>
      <div class="card kpi"><div class="k-label">👷 開工至今</div>
        <div class="k-value">{days_since_start:,} <span style="font-size:1rem;color:#8A9587;">天</span></div>
        <div class="k-sub">開工 {start_date:%Y-%m-%d}</div></div>
      <div class="card kpi"><div class="k-label">📋 勘驗紀錄</div>
        <div class="k-value">{len(df)} <span style="font-size:1rem;color:#8A9587;">筆</span></div>
        <div class="k-sub">自動同步建管系統</div></div>
    </div>
    """)

    col_building, col_road = st.columns([1, 1.25], gap="large")

    # --- 🏢 樓層剖面圖 ---
    with col_building:
        st.markdown("**🏢 樓層剖面圖**")
        fh, w, left = 13, 170, 52
        n_total = TOTAL_FLOORS + BASEMENT_FLOORS
        top = 18
        height = top + n_total * fh + 30
        parts = []
        for i in range(n_total):
            floor = TOTAL_FLOORS - i if i < TOTAL_FLOORS else -(i - TOTAL_FLOORS + 1)
            y = top + i * fh + (6 if floor < 0 else 0)
            if floor > 0:
                done = floor <= current_floor
                fill = "#FFB020" if floor == current_floor else ("#5FA82E" if done else "#FFFFFF")
            else:
                done = -floor <= basement_done
                fill = "#8C6D4F" if done else "#FFFFFF"
            parts.append(f"<rect x='{left}' y='{y}' width='{w}' height='{fh - 2}' rx='2' fill='{fill}' stroke='#C9D3C4' stroke-width='1'/>")
            if floor in (TOTAL_FLOORS, 20, 15, 10, 5, 1) or floor == -1 or floor == -BASEMENT_FLOORS:
                label = f"{floor}F" if floor > 0 else f"B{-floor}"
                parts.append(f"<text x='{left - 8}' y='{y + fh - 4}' text-anchor='end' font-size='10' fill='#6B7768'>{label}</text>")
            if floor == current_floor and current_floor > 0:
                parts.append(f"<text x='{left + w + 8}' y='{y + fh - 3}' font-size='11' font-weight='700' fill='#B57400'>◀ 目前 {current_floor}F</text>")
        ground_y = top + TOTAL_FLOORS * fh + 2
        parts.append(f"<line x1='10' x2='{left + w + 40}' y1='{ground_y}' y2='{ground_y}' stroke='#6B7768' stroke-dasharray='4 3'/>")
        parts.append(f"<text x='{left + w + 8}' y='{ground_y + 4}' font-size='10' fill='#6B7768'>地面</text>")
        legend_y = height - 8
        parts.append(f"<rect x='{left}' y='{legend_y - 9}' width='10' height='10' fill='#5FA82E'/><text x='{left + 14}' y='{legend_y}' font-size='10' fill='#4A5547'>已完成</text>")
        parts.append(f"<rect x='{left + 60}' y='{legend_y - 9}' width='10' height='10' fill='#FFB020'/><text x='{left + 74}' y='{legend_y}' font-size='10' fill='#4A5547'>最新</text>")
        parts.append(f"<rect x='{left + 110}' y='{legend_y - 9}' width='10' height='10' fill='#fff' stroke='#C9D3C4'/><text x='{left + 124}' y='{legend_y}' font-size='10' fill='#4A5547'>未施工</text>")
        show_html(f"<div class='card' style='text-align:center;'><svg viewBox='0 0 {left + w + 80} {height}' style='width:100%;max-width:340px;' role='img' aria-label='樓層剖面圖'>{''.join(parts)}</svg></div>")

    # --- 🗺️ 工程階段 ---
    with col_road:
        st.markdown("**🗺️ 工程階段**")
        underground_done_date = below['掛號日期'].max() if not below.empty else None
        stages = [
            {"name": "開工與基礎工程", "status": "done", "note": f"{start_date:%Y-%m-%d} 開工"},
            {"name": f"地下室結構 (B{BASEMENT_FLOORS}～B1)",
             "status": "done" if basement_done >= BASEMENT_FLOORS else ("doing" if basement_done else "todo"),
             "note": f"B1 頂版 {underground_done_date:%Y-%m-%d} 勘驗" if basement_done >= BASEMENT_FLOORS and underground_done_date is not None else ""},
            {"name": f"地上結構體 (1F～{TOTAL_FLOORS}F)",
             "status": "done" if current_floor >= TOTAL_FLOORS else ("doing" if current_floor else "todo"),
             "note": f"目前 {current_floor}F / {TOTAL_FLOORS}F", "bar": progress_ratio},
            {"name": "結構封頂", "status": "done" if current_floor >= TOTAL_FLOORS else "todo",
             "note": f"若維持近期節奏，參考約 {structure_estimate}" if structure_estimate else ""},
        ] + LATER_STAGES

        items = []
        step = 0
        for s in stages:
            step += 1
            status = s.get("status", "todo")
            icon = "✓" if status == "done" else str(step)
            status_text = {"done": "已完成", "doing": "進行中", "todo": "尚未開始"}.get(status, "")
            bar = f"<div class='bar'><div style='width:{s['bar'] * 100:.0f}%'></div></div>" if "bar" in s and status == "doing" else ""
            note = f"<div class='r-note'>{esc(s['note'])}</div>" if s.get("note") else ""
            items.append(f"<li><div class='dot dot-{status}'>{icon}</div><div><div class='r-name'>{esc(s['name'])} "
                         f"<span class='muted'>・{status_text}</span></div>{note}{bar}</div></li>")
        show_html(f"<div class='card'><ul class='roadmap'>{''.join(items)}</ul></div>")
        st.caption("ℹ️ 結構封頂之後的階段（外牆、內裝、拆鷹架、使用執照、交屋）在建管勘驗資料中查不到，"
                   "將由站長依公開資訊手動更新。本站不推估交屋日期，實際時程請以建商正式公告為準。")

    # --- 📈 施工爬升曲線 ---
    if len(slabs) >= 2:
        st.markdown("**📈 施工爬升曲線**　<span class='muted'>每個點是一次頂版勘驗，線越陡代表蓋得越快</span>", unsafe_allow_html=True)
        chart_df = slabs[['掛號日期', '樓層', '勘驗項目', '審核進度']].copy()
        y_scale = alt.Scale(domain=[-BASEMENT_FLOORS - 1, TOTAL_FLOORS + 2])
        base = alt.Chart(chart_df).encode(
            x=alt.X('掛號日期:T', title=None, axis=alt.Axis(format='%Y/%m', tickCount='month', labelAngle=0)),
            y=alt.Y('樓層:Q', title=None, scale=y_scale,
                    axis=alt.Axis(values=[-BASEMENT_FLOORS, 0] + list(range(5, TOTAL_FLOORS + 1, 5)), labelExpr="datum.value < 0 ? 'B' + -datum.value : datum.value == 0 ? '地面' : datum.value + 'F'")),
            tooltip=[alt.Tooltip('掛號日期:T', title='掛號日期', format='%Y-%m-%d'),
                     alt.Tooltip('勘驗項目:N', title='勘驗項目'),
                     alt.Tooltip('審核進度:N', title='審核進度')],
        )
        line = base.mark_line(color='#5FA82E', strokeWidth=3)
        points = base.mark_point(color='#5FA82E', filled=True, size=70)
        rules = pd.DataFrame({'y': [0, TOTAL_FLOORS], 'label': ['', f'頂樓 {TOTAL_FLOORS}F']})
        rule = alt.Chart(rules).mark_rule(color='#9AA596', strokeDash=[4, 4]).encode(y='y:Q')
        rule_text = alt.Chart(rules).mark_text(align='left', dx=4, dy=-6, color='#6B7768', fontSize=11).encode(
            y='y:Q', x=alt.value(0), text='label:N')
        st.altair_chart((rule + rule_text + line + points).properties(height=300), use_container_width=True)

# ==========================================
# 📜 分頁二：施工紀錄 (時間軸)
# ==========================================
def photo_strip(item):
    rows = photos[photos['勘驗項目'] == item]
    if rows.empty:
        return ""
    thumbs = []
    for _, p in rows.iterrows():
        url = photo_url(p['檔名'])
        tip = esc(f"{p['標題']}｜{p['說明']}")
        thumbs.append(f"<a href='{esc(url)}' target='_blank' title='{tip}'>"
                      f"<img loading='lazy' src='{esc(img_src(url, 400))}' alt='{tip}'></a>")
    return f"<div class='strip'>{''.join(thumbs)}</div><div class='muted' style='margin-top:4px;'>📷 {len(rows)} 張照片，點圖看原圖</div>"


with tab_records:
    st.caption("由新到舊排列。資料每天自動向新北市建管系統同步兩次。")
    newest_first = df.sort_values('掛號日期', ascending=False).reset_index(drop=True)
    blocks = []
    current_year = None
    for idx, row in newest_first.iterrows():
        year = row['掛號日期'].year
        if year != current_year:
            blocks.append(f"<div class='year'>{year}</div>")
            current_year = year
        latest_cls = " is-latest" if idx == 0 else ""
        latest_tag = "<span class='badge b-ok' style='margin-left:6px;'>最新</span>" if idx == 0 else ""
        blocks.append(f"""
        <div class="tl{latest_cls}">
          <div class="date">{row['掛號日期']:%m/%d}<span>{row['掛號日期']:%Y}</span></div>
          <div class="card">
            <div class="t-title">{esc(display_item(row['勘驗項目']))}{latest_tag}</div>
            <div>{badge(row['審核進度'])} <span class="muted">　掛號號碼 {esc(row['掛號號碼'])}</span></div>
            {photo_strip(row['勘驗項目'])}
          </div>
        </div>""")
    show_html("".join(blocks))

# ==========================================
# 📸 分頁三：相簿
# ==========================================
with tab_album:
    st.link_button("☁️ 前往 Google Drive 看【光茵築夢全紀錄】完整相簿", MASTER_ALBUM_URL, use_container_width=True)
    if photos.empty:
        st.info("目前還沒有精選照片。")
    else:
        order = df.sort_values('掛號日期', ascending=False)
        date_of = dict(zip(order['勘驗項目'], order['掛號日期']))
        groups = sorted(photos['勘驗項目'].unique(), key=lambda k: date_of.get(k, pd.Timestamp.min), reverse=True)
        for g in groups:
            rows = photos[photos['勘驗項目'] == g]
            d = date_of.get(g)
            date_txt = f"　<span class='muted'>{d:%Y-%m-%d}</span>" if d is not None else ""
            figs = []
            for _, p in rows.iterrows():
                url = photo_url(p['檔名'])
                figs.append(f"<figure><a href='{esc(url)}' target='_blank'><img loading='lazy' src='{esc(img_src(url, 600))}' "
                            f"alt='{esc(p['標題'])}'></a><figcaption><b>{esc(p['標題'])}</b>{esc(p['說明'])}</figcaption></figure>")
            show_html(f"<div class='year' style='font-size:1rem;'>📌 {esc(display_item(g))}{date_txt}</div>"
                      f"<div class='gallery'>{''.join(figs)}</div>")
        st.caption("📷 照片由芳鄰熱情提供，點圖可看原始大圖。歡迎分享您拍到的工地照片！")

# ==========================================
# ℹ️ 分頁四：關於本站
# ==========================================
with tab_about:
    line_btn = (f"<p><a class='btn btn-line' href='{esc(LINE_ADD_FRIEND_URL)}' target='_blank'>💬 加入 LINE 官方帳號，新進度自動通知</a></p>"
                if LINE_ADD_FRIEND_URL else "")
    show_html(f"""
    <div class="card">
      <p><b>{esc(SITE_TITLE)}</b> 是由芳鄰自發製作的工程進度紀錄站，{esc(AUTHOR_NOTE)}。</p>
      <p>系統每天自動到 <b>新北市政府工務局建管系統</b> 查詢本案的施工勘驗紀錄，
      當有新樓層的勘驗通過「同意備查」時，會透過 LINE 通知加入的芳鄰。</p>
      {line_btn}
      <div style="background:#FFF8E6;border:1px solid #F2DDA4;border-radius:10px;padding:10px 14px;margin:12px 0;">
      <b>📢 非官方聲明</b><br>
      本站為住戶自發建立的非官方網站，與馥華集團及建案相關公司無任何隸屬或合作關係。
      工程資料取自新北市政府建管系統公開資訊，照片由芳鄰提供；內容僅供參考，
      一切以建商及主管機關正式公告為準。本站不推估交屋日期。
      </div>
      <p class="muted">👁️ 累計瀏覽：<img style="vertical-align:middle;" alt="views"
      src="https://hits.sh/{esc(COUNTER_KEY)}.svg?label=芳鄰瀏覽&color=5FA82E&labelColor=555555"></p>
    </div>
    """)
