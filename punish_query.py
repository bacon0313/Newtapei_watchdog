"""
幼兒園裁罰紀錄查詢工具
資料來源：全國教保資訊網 - 裁罰紀錄查詢
https://ap.ece.moe.edu.tw/webecems/punishSearch.aspx

用法：
    python punish_query.py            # 互動模式，會提示輸入學校名稱
    python punish_query.py 人愛        # 直接查詢「人愛」相關幼兒園
    python punish_query.py 人愛 --city 基隆市  # 限定縣市
    python punish_query.py 人愛 --detail      # 自動開啟瀏覽器並顯示查詢連結

說明：
    這個系統只收錄「有裁罰紀錄」的幼兒園。
    - 查得到  → 該園有裁罰紀錄
    - 查不到  → 查無裁罰紀錄
    
    使用 --detail 可自動開啟瀏覽器，並顯示線上查詢、電話等替代方案。
    
詳細內容的限制：
    全國教保資訊網的詳細裁罰記錄頁面需要身份驗證或特殊授權。
    如需查詢詳細內容，可：
    1. 直接訪問官網查詢：https://www.ece.moe.edu.tw/
    2. 撥打幼兒園電話詢問
    3. 洽詢當地教育處
"""
import sys
import re
import argparse
import requests
import urllib3
from bs4 import BeautifulSoup
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SEARCH_URL = "https://ap.ece.moe.edu.tw/webecems/punishSearch.aspx"
VIEW_BASE = "https://ap.ece.moe.edu.tw/webecems/dtl/punish_view.aspx?sch="

# 縣市名稱 -> 網站代碼
CITY_CODES = {
    "基隆市": "01", "臺北市": "02", "台北市": "02", "新北市": "03",
    "桃園市": "05", "新竹市": "06", "新竹縣": "07", "苗栗縣": "08",
    "臺中市": "09", "台中市": "09", "彰化縣": "11", "南投縣": "12",
    "雲林縣": "13", "嘉義市": "14", "嘉義縣": "15", "臺南市": "16",
    "台南市": "16", "高雄市": "18", "屏東縣": "20", "臺東縣": "21",
    "台東縣": "21", "花蓮縣": "22", "宜蘭縣": "04", "澎湖縣": "23",
    "金門縣": "24", "連江縣": "25",
}


def _hidden(soup, name):
    el = soup.find("input", {"name": name})
    return el["value"] if el and el.has_attr("value") else ""


def query_penalty(school_name, city=None):
    """查詢學校裁罰紀錄，回傳 list[dict]。空 list 代表查無紀錄。"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36"),
    })

    # 1. 取得表單隱藏欄位
    r = session.get(SEARCH_URL, verify=False, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    city_code = ""
    if city:
        city_code = CITY_CODES.get(city.strip(), "")
        if not city_code:
            print(f"[提醒] 無法辨識縣市「{city}」，改以全國查詢。")

    payload = {
        "__VIEWSTATE": _hidden(soup, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _hidden(soup, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _hidden(soup, "__EVENTVALIDATION"),
        "ddlKey": "school_name",
        "txtKeyNameS": school_name,
        "ddlCityS": city_code,
        "ddlAreaS": "",
        "btnSearch": "搜尋",
    }

    # 2. 送出查詢
    r2 = session.post(SEARCH_URL, data=payload, verify=False, timeout=30)
    r2.raise_for_status()
    r2.encoding = "utf-8"

    return _parse_results(r2.text)


def _parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # 每筆結果的學校名稱 span id 為 GridView1_lblSchName_N
    name_spans = soup.find_all("span", id=lambda x: x and "lblSchName" in x)
    for span in name_spans:
        idx = span.get("id").split("_")[-1]  # 取得列索引

        def field(key):
            el = soup.find("span", id=f"GridView1_{key}_{idx}")
            return el.get_text(strip=True) if el else ""

        # 檢視連結中的 sch token → 明細頁網址
        detail_url = None
        view_link = soup.find("a", id=f"GridView1_lbView_{idx}")
        if view_link and view_link.has_attr("onclick"):
            m = re.search(r"punish_view\.aspx\?sch=([A-Za-z0-9+/=]+)",
                          view_link["onclick"])
            if m:
                detail_url = VIEW_BASE + m.group(1)

        results.append({
            "school": span.get_text(strip=True),
            "city": field("lblCity"),
            "area": field("lblArea"),
            "public": field("lblPub"),
            "tel": field("lblTel"),
            "capacity": field("lblGenStd"),
            "status": field("lblBStatus"),
            "has_penalty": detail_url is not None,
            "detail_url": detail_url,
        })

    return results


def print_report(school_name, results):
    print("=" * 60)
    print(f"查詢學校關鍵字：{school_name}")
    print("=" * 60)

    if not results:
        print("結果：查無裁罰紀錄")
        print("（此系統僅收錄有裁罰紀錄的幼兒園，查不到表示無裁罰紀錄，")
        print("  或請確認學校名稱是否正確、可只輸入部分關鍵字。）")
        return

    print(f"結果：找到 {len(results)} 筆裁罰紀錄\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['school']}")
        print(f"    縣市鄉鎮：{r['city']} {r['area']}")
        print(f"    設立別　：{r['public']}")
        print(f"    電話　　：{r['tel']}")
        print(f"    核定人數：{r['capacity']}")
        print(f"    營運狀態：{r['status']}")
        print(f"    裁罰紀錄：有")
        if r["detail_url"]:
            print(f"    裁罰明細：{r['detail_url']}")
        print()


def fetch_detail_records(results):
    """使用 Selenium 抓取 JavaScript 動態載入的裁罰紀錄"""
    print("[提示] 正在自動開啟瀏覽器抓取詳細內容...\n")
    print("[說明] 網站頁面內容受到保護需要登錄授權\n")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as e:
        print(f"[錯誤] 缺少必要模組: {e}")
        return
    
    # 設定 Chrome 選項
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-popup-blocking")
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        for i, result in enumerate(results, 1):
            if not result.get("detail_url"):
                continue
            
            print(f"[{i}] {result['school']} 的裁罰紀錄")
            print("-" * 60)
            print(f"網址: {result['detail_url']}")
            print()
            print("瀏覽器已自動開啟此頁面。")
            print("由於頁面需要登錄授權，以下為替代方案：")
            print()
            print("1. 📱 線上查詢（推薦）")
            print("   請到全國教保資訊網自行查詢：")
            print("   https://www.ece.moe.edu.tw/")
            print()
            print("2. 📞 電話查詢")
            print(f"   學校電話：{result['tel']}")
            print()
            print("3. 📧 相關單位")
            print(f"   {result['city']} 教育處 (幼兒園承辦課室)")
            print()
    
    except Exception as e:
        print(f"[錯誤] {e}")
    
    finally:
        if driver:
            try:
                # 保持瀏覽器開啟，讓使用者有機會手動查看
                input("\n按 Enter 鍵關閉瀏覽器...")
                driver.quit()
            except:
                pass



def main():
    parser = argparse.ArgumentParser(
        description="幼兒園裁罰紀錄查詢（資料來源：全國教保資訊網）")
    parser.add_argument("school", nargs="?", help="學校名稱關鍵字")
    parser.add_argument("--city", help="限定縣市，例如：新北市")
    parser.add_argument("--detail", action="store_true", 
                        help="抓取詳細裁罰紀錄內容（使用 Selenium）")
    args = parser.parse_args()

    school = args.school
    if not school:
        try:
            school = input("請輸入學校名稱：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
    if not school:
        print("未輸入學校名稱，結束。")
        return

    try:
        results = query_penalty(school, args.city)
    except requests.RequestException as e:
        print(f"[錯誤] 連線失敗：{e}")
        return

    print_report(school, results)
    
    # 如果要詳細內容，使用 Selenium 抓取
    if args.detail and results:
        print("\n" + "=" * 60)
        print("正在抓取詳細裁罰紀錄...")
        print("=" * 60)
        fetch_detail_records(results)


if __name__ == "__main__":
    main()
