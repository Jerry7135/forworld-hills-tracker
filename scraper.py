import requests, json, os, sys, urllib3, time, ddddocr
from bs4 import BeautifulSoup
import pandas as pd
from collections import OrderedDict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# ⚙️ 系統設定區 (改由 GitHub 保險箱讀取密碼)
# ==========================================
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
# USER_ID 變數保留，但廣播功能已經不需要用到它了
USER_ID = os.getenv("LINE_USER_ID")

# 判斷是否為「GitHub 網頁上手動按下的測試按鈕」
FORCE_TEST = os.getenv("FORCE_TEST", "false") == "true"

def send_line_message(msg_text):
    """使用 LINE Messaging API (機器人) 發送【廣播訊息】給所有好友"""
    if not CHANNEL_ACCESS_TOKEN:
        print("⚠️ 找不到 CHANNEL_ACCESS_TOKEN，跳過 LINE 通知。")
        return
        
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    
    # 廣播不需要指定 "to"，LINE 會自動發給所有加機器人為好友的人
    data = {"messages": [{"type": "text", "text": msg_text}]}
    
    try:
        requests.post(url, headers=headers, data=json.dumps(data))
    except Exception as e:
        print(f"❗ LINE 廣播發送失敗: {e}")

def fetch_ntpc_data():
    session = requests.Session()
    ocr = ddddocr.DdddOcr(show_ad=False)
    host = "https://building-management.publicwork.ntpc.gov.tw"
    target_url = f"{host}/ph_list.jsp" 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': f"{host}/", 'Origin': host,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    for _ in range(3):
        try:
            session.get(f"{host}/", headers=headers, verify=False, timeout=15)
            time.sleep(1)
            captcha_url = f"{host}/ImageServlet?time={int(time.time() * 1000)}"
            captcha_res = session.get(captcha_url, headers=headers, verify=False)
            captcha_code = ocr.classification(captcha_res.content)
            payload = OrderedDict([
                ('I1', '111'), ('I2', '00335'), ('E1V', '請選擇...'), 
                ('E1', ''), ('E2V', '請選擇...'), ('E2', ''), 
                ('E3', ''), ('E4', ''), ('Z1', captcha_code)
            ])
            response = session.post(target_url, data=payload, headers=headers, timeout=60, verify=False)
            response.encoding = 'utf-8'
            if "資料列示" in response.text or "footable-grid" in response.text:
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', id='footable-grid')
                if not table: return pd.DataFrame()
                rows = table.find('tbody').find_all('tr')
                results = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 5: continue
                    status = cols[4].get_text(strip=True)
                    if "退請補正" in status: continue
                    case_info = cols[1].get_text(separator=' ', strip=True)
                    app_type = cols[2].get_text(separator=' ', strip=True)
                    try:
                        date_v = case_info.split('掛號日期：')[1].split(' ')[0]
                        case_v = case_info.split('掛號號碼：')[1].strip()
                        item_v = app_type.replace("施工勘驗 勘驗項目：", "").strip()
                        results.append({'掛號日期': date_v, '掛號號碼': case_v, '勘驗項目': item_v, '審核進度': status})
                    except: continue
                return pd.DataFrame(results)
            time.sleep(5)
        except Exception: time.sleep(5)
    return pd.DataFrame()

def job():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🤖 啟動雲端監工機器人...")
    new_df = fetch_ntpc_data()
    if new_df.empty:
        print("💀 解析失敗。")
        return

    file_name = 'history.csv'
    has_update = False
    
    if os.path.exists(file_name):
        old_df = pd.read_csv(file_name)
        if len(new_df) > len(old_df) or not new_df.astype(str).equals(old_df.astype(str)):
            has_update = True
    else:
        has_update = True

    # 🎯 如果是你在 GitHub 按下手動測試，無條件視為「有更新」來發送！
    if FORCE_TEST:
        print("🔧 [手動測試模式] 強制發送最新進度！")
        has_update = True

    if has_update:
        new_df.to_csv(file_name, index=False, encoding='utf-8-sig')
        sorted_df = new_df.sort_values(by='掛號日期', ascending=False)
        latest_row = sorted_df.iloc[0]
        
        # 🎯 在這裡設定你未來的網頁網址 (現在可以先放個假網址或留空)
        website_url = "https://你的光茵專屬網頁.com" 

        msg = ""
        if FORCE_TEST:
            msg = (f"\n🔔 [系統手動測試] 親愛的芳鄰，讓我們一起紀錄與期待光茵的落成！\n"
                   f"✅ 目前最新進度：\n"
                   f"📌 項目：{latest_row['勘驗項目']}\n"
                   f"🚥 狀態：{latest_row['審核進度']}\n"
                   f"📅 日期：{latest_row['掛號日期']}\n"
                   f"🌐 光茵築夢日記網頁：https://forworld-hills-schedule.streamlit.app/") # 👈 這裡加上網址
        else:
            msg = (f"\n🏢 【馥華之丘-光茵】出現新進度啦！\n"
                   f"📌 勘驗項目：{latest_row['勘驗項目']}\n"
                   f"🚥 審核進度：{latest_row['審核進度']}\n"
                   f"📅 掛號日期：{latest_row['掛號日期']}\n"
                   f"📊 目前累積：共 {len(new_df)} 筆\n"
                   f"🌐 光茵築夢日記網頁：https://forworld-hills-schedule.streamlit.app/") # 👈 這裡加上網址
              
        send_line_message(msg)
        print(f"🎉 發現異動或測試！已推播：{latest_row['勘驗項目']}")
    else:
        print("💤 沒有新增進度，不發送通知。")

if __name__ == "__main__":
    job()





