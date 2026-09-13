"""
app.py  ── 新北市教育局 Smart Watchdog 智慧風險預警管理系統
使用 Streamlit 建立儀表板
"""
import json
import time
import urllib.parse
import re
import boto3
import streamlit as st

# ── 頁面設定 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Watchdog 智慧風險預警",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全域樣式（科技感藍紫色調）────────────────────────────────────────────────
st.markdown("""
<style>
/* 整體背景 */
.stApp { background: #0a0e1a; color: #e0e8ff; }
[data-testid="stSidebar"] { background: #0f1628; border-right: 1px solid #1e2d5a; }

/* 標題列 */
.main-header {
    background: linear-gradient(135deg, #1a2b6b 0%, #2d1b69 50%, #0f4c81 100%);
    padding: 18px 28px; border-radius: 12px;
    border: 1px solid #3a5bd4;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(58,91,212,0.3);
}
.main-header h1 { color: #7eb8ff; font-size: 2.2rem; margin:0; letter-spacing:.5px; font-weight:800; }
.main-header p  { color: #9bb4e8; font-size:1rem; margin:8px 0 0; }

/* 側欄標籤 */
.sidebar-label { color:#7eb8ff; font-weight:600; font-size:.9rem; margin-bottom:4px; }

/* 功能選單標題（放大） */
.menu-title {
    color:#8fc0ff; font-weight:800; font-size:1.35rem;
    letter-spacing:1px; margin:4px 0 14px;
}

/* ── 功能選單：長條型頁簽 ────────────────────────────────────── */
/* 讓 radio 選項垂直排列、每個佔滿整寬 */
[data-testid="stSidebar"] div[role="radiogroup"] {
    display:flex; flex-direction:column; gap:10px;
}
/* 每個選項做成長條卡片 */
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    display:flex; align-items:center;
    width:100%; box-sizing:border-box;
    padding:14px 18px;
    background:#111b35;
    border:1px solid #24356b;
    border-radius:12px;
    cursor:pointer;
    transition:all .15s ease;
    font-size:1.05rem; font-weight:600;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    border-color:#3a5bd4; background:#16224a;
}
/* 隱藏原本的圓形 radio 圈 */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display:none !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label p {
    font-size:1.05rem !important; font-weight:600 !important; color:#dbe6ff !important;
}
/* 選中的長條高亮（藍紫漸層 + 左側標記） */
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background:linear-gradient(135deg,#1a2b6b,#2d1b69);
    border-color:#5b7bff;
    box-shadow:0 0 0 1px #5b7bff inset, 0 4px 14px rgba(58,91,212,.35);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
    color:#ffffff !important;
}

/* 財務特徵卡片 */
.fin-card {
    background:#111b35; border:1px solid #1e3a6e; border-radius:10px;
    padding:14px 18px; margin:6px 0;
}
.fin-card .label { color:#8ab4f8; font-size:.8rem; }
.fin-card .value { color:#e8f0ff; font-size:1.2rem; font-weight:700; }

/* 風險卡片 */
.risk-0 { background:linear-gradient(135deg,#0d3321,#0a4a2a); border:2px solid #22c55e; border-radius:14px; padding:24px; text-align:center; }
.risk-1 { background:linear-gradient(135deg,#2d2800,#3d3500); border:2px solid #eab308; border-radius:14px; padding:24px; text-align:center; }
.risk-2 { background:linear-gradient(135deg,#2d1500,#3d1f00); border:2px solid #f97316; border-radius:14px; padding:24px; text-align:center; }
.risk-3 { background:linear-gradient(135deg,#2d0000,#3d0000); border:2px solid #ef4444; border-radius:14px; padding:24px; text-align:center; }
.risk-label { font-size:2rem; font-weight:800; margin:8px 0; }
.risk-sub   { font-size:.9rem; opacity:.85; }

/* 四格風險等級網格 */
.risk-grid {
    display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:6px 0 4px;
}
.risk-cell {
    position:relative; border:2px solid; border-radius:14px;
    padding:18px 10px; text-align:center; background:#0f1730;
    transition:all .2s ease;
}
.risk-cell-on  { background:linear-gradient(135deg,#141f42,#1c1440); transform:translateY(-2px); }
.risk-cell-off { opacity:.38; filter:grayscale(35%); }
.risk-cell .rc-icon   { font-size:2.2rem; line-height:1; }
.risk-cell .rc-en     { font-size:1.15rem; font-weight:800; margin:6px 0 2px; letter-spacing:.5px; }
.risk-cell .rc-name   { font-size:.95rem; font-weight:600; color:#dbe6ff; }
.risk-cell .rc-action { font-size:.78rem; color:#9bb4e8; margin-top:4px; }
.risk-cell .rc-badge  {
    position:absolute; top:-10px; left:50%; transform:translateX(-50%);
    color:#0a0e1a; font-size:.72rem; font-weight:800;
    padding:2px 10px; border-radius:10px; white-space:nowrap;
}
/* 手機窄螢幕改兩欄 */
@media (max-width: 640px) {
    .risk-grid { grid-template-columns:repeat(2,1fr); }
}

/* 進度條覆蓋 */
.stProgress > div > div { background:#3a5bd4; }

/* ── 自訂載入旋轉圈 ────────────────────────────────────────── */
@keyframes wd-spin { 0%{transform:rotate(0)} 100%{transform:rotate(360deg)} }
.wd-loader-wrap {
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:16px; padding:36px 20px; margin:8px 0;
    background:#111b35; border:1px solid #24356b; border-radius:14px;
}
.wd-spinner {
    width:64px; height:64px; border-radius:50%;
    border:6px solid #1e2d5a;
    border-top-color:#5b7bff; border-right-color:#8b5cf6;
    animation:wd-spin .8s linear infinite;
}
.wd-loader-text { color:#bcd0ff; font-size:1.05rem; font-weight:600; letter-spacing:.5px; }
.wd-loader-sub  { color:#7f93c4; font-size:.82rem; }

/* 強化 Streamlit 內建 spinner 的可見度（放大旋轉圈、亮色） */
[data-testid="stSpinner"] {
    display:flex !important; flex-direction:row !important;
    align-items:center !important; gap:12px !important;
    flex-wrap:nowrap !important;
}
.stSpinner > div, [data-testid="stSpinner"] > div:first-child {
    border-top-color:#5b7bff !important;
    border-right-color:#8b5cf6 !important;
    width:2.2rem !important; height:2.2rem !important;
    flex:0 0 auto !important;
}
[data-testid="stSpinner"] p, .stSpinner p {
    color:#bcd0ff !important; font-weight:600;
    white-space:nowrap !important;     /* 文字不逐字換行 */
    margin:0 !important;
}

/* 審計建議區 */
.audit-box {
    background:#111b35; border:1px solid #2a4080; border-radius:10px;
    padding:20px; margin-top:8px; line-height:1.7; color:#d0dcf5;
}

/* Section 標題 */
.sec-title {
    color:#7eb8ff; font-size:1rem; font-weight:700;
    border-bottom:1px solid #1e3a6e; padding-bottom:6px; margin:16px 0 12px;
}

/* ── 隱藏頂部白色工具列 / header ────────────────────────────── */
header[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }   /* 頂部彩色/白色細條 */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.block-container { padding-top: 1.5rem; }

/* ── 側邊欄固定、禁止收合 ────────────────────────────────────── */
/* 隱藏收合（<<）按鈕 */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
/* 側邊欄固定寬度、永遠展開 */
[data-testid="stSidebar"] {
    min-width: 300px !important;
    max-width: 300px !important;
    transform: none !important;
    visibility: visible !important;
}

/* ══ 文字可讀性：兜底規則 ══ */
/* 主畫面與側欄「所有」文字元素預設亮色，避免任何漏網之魚 */
.stApp, .stApp *,
[data-testid="stSidebar"], [data-testid="stSidebar"] * {
    color:#e2ebff !important;
}

/* 標題 h1-h6 */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color:#eaf1ff !important;
}

/* caption / 小字略淡但仍清楚 */
.stCaption, [data-testid="stCaptionContainer"], .stApp small {
    color:#aebfe8 !important;
}

/* placeholder */
.stApp input::placeholder, .stApp textarea::placeholder {
    color:#7387b8 !important;
}

/* 輸入框 / textarea 背景 */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    color:#eaf1ff !important; background:#111b35 !important;
    border:1px solid #2a4080 !important;
}

/* selectbox 收合時顯示的方塊 */
[data-baseweb="select"] > div {
    background:#111b35 !important; border-color:#2a4080 !important;
}

/* file uploader 區塊 */
[data-testid="stFileUploader"] section {
    background:#111b35 !important; border:1px dashed #3a5bd4 !important;
}

/* selectbox / multiselect 展開的下拉選單（深底 + 亮字）*/
[data-baseweb="popover"], ul[role="listbox"] {
    background:#111b35 !important;
}
[data-baseweb="popover"] *, ul[role="listbox"] *,
ul[role="listbox"] li, li[role="option"] {
    color:#e8f0ff !important;
    background:transparent !important;
}
/* 滑鼠移過/選中的選項高亮 */
li[role="option"]:hover, li[aria-selected="true"] {
    background:#1e2d5a !important;
}
/* info / success / warning / error 提示方塊：深底 + 亮字（配深色主題） */
[data-testid="stAlert"] {
    background:#111b35 !important;
    border:1px solid #3a5bd4 !important;
    border-radius:10px !important;
}
[data-testid="stAlert"] * {
    color:#e6eeff !important;
}
/* 依語意微調左側邊框顏色 */
[data-testid="stAlert"]:has(svg) { border-left-width:4px !important; }
/* success（綠） */
[data-testid="stAlertContentSuccess"], .stAlertContentSuccess { color:#c7f9d8 !important; }
div[data-baseweb="notification"] { background:#111b35 !important; }
/* primary 按鈕（藍/紅底）文字用白色 */
.stButton button[kind="primary"], .stDownloadButton button[kind="primary"],
.stButton button[data-testid="baseButton-primary"] {
    color:#ffffff !important;
}
.stButton button[kind="primary"] * { color:#ffffff !important; }

/* secondary 按鈕：給深底 + 亮字，確保清楚 */
.stButton button[kind="secondary"], .stDownloadButton button {
    background:#1a2b6b !important;
    color:#eaf1ff !important;
    border:1px solid #3a5bd4 !important;
}
.stButton button[kind="secondary"] *, .stDownloadButton button * {
    color:#eaf1ff !important;
}
/* 通用防呆：任何「淺色底」按鈕改用黑字（偵測白/淺底時） */
.stButton button[style*="background: rgb(255"] ,
.stButton button[style*="background-color: rgb(255"] {
    color:#0a0e1a !important;
}
.stButton button[style*="background: rgb(255"] * ,
.stButton button[style*="background-color: rgb(255"] * {
    color:#0a0e1a !important;
}
</style>
""", unsafe_allow_html=True)

# ── AWS 設定 ──────────────────────────────────────────────────────────────────
REGION        = "us-west-2"
KB_ID         = "O3JQQHDGJO"
ENDPOINT_NAME = "watchdog-risk-endpoint-lukew"
MODEL_ID      = "us.anthropic.claude-sonnet-4-20250514-v1:0"

RISK_CONFIG = {
    0: {"cls":"risk-0","icon":"🟢","name":"低風險 Safe",      "en":"SAFE",     "action":"例行監測"},
    1: {"cls":"risk-1","icon":"🟡","name":"注意風險 Warning", "en":"WARNING",  "action":"持續追蹤"},
    2: {"cls":"risk-2","icon":"🟠","name":"高風險 Alert",     "en":"ALERT",    "action":"加強查核"},
    3: {"cls":"risk-3","icon":"🔴","name":"極高風險 Critical","en":"CRITICAL", "action":"優先稽查"},
}


from contextlib import contextmanager

@contextmanager
def loading(text="處理中…", sub="請稍候，系統正在運算"):
    """在等待期間顯示置中的大旋轉圈 + 文字；結束後自動清除。"""
    ph = st.empty()
    ph.markdown(
        f'<div class="wd-loader-wrap"><div class="wd-spinner"></div>'
        f'<div class="wd-loader-text">{text}</div>'
        f'<div class="wd-loader-sub">{sub}</div></div>',
        unsafe_allow_html=True)
    try:
        yield
    finally:
        ph.empty()


# ── 幼兒園名單（從 S3 檔名擷取，含所有學年度）────────────────────────────────
@st.cache_data(show_spinner=False)
def load_kindergarten_list():
    s3 = boto3.client("s3", region_name=REGION)
    paginator = s3.get_paginator("list_objects_v2")
    gardens = {}  # name -> {year -> key}
    for page in paginator.paginate(Bucket="s3-education-0912", Prefix="資料集/非營利園財報/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            fname = urllib.parse.unquote(key.split("/")[-1]).replace(".pdf", "")
            # 格式：N01安溪_111學年度財務報告
            m = re.match(r"(N\d+)(.+?)_(\d+)學年度", fname)
            if m:
                code, gname, year = m.group(1), m.group(2), m.group(3)
                full = f"{gname}非營利幼兒園" if "幼兒園" not in gname else gname
                display = f"{code} {gname}"
                if display not in gardens:
                    gardens[display] = {"name": full, "code": code, "years": {}}
                gardens[display]["years"][year] = key
    return gardens

# ── 從 S3 下載 PDF 原始 bytes（供下載按鈕使用，帶快取）──────────────────────
@st.cache_data(show_spinner=False)
def fetch_pdf_bytes(s3_key):
    try:
        s3 = boto3.client("s3", region_name=REGION)
        return s3.get_object(Bucket="s3-education-0912", Key=s3_key)["Body"].read()
    except Exception:
        return None


# ── 財務特徵擷取：直接對原始 PDF 做 Claude 視覺解析 ───────────────────────────
@st.cache_data(show_spinner=False)
def extract_financials_from_pdf(s3_key, garden_name, year, _progress_key=""):
    """
    從 S3 下載該園所該學年度的 PDF，逐頁（含表格的頁）用 Claude 視覺模型
    解析出：教保費收入預算/決算、人事費預算/決算，回傳 4 個特徵。
    這些 PDF 多為掃描圖，KB 文字檢索抓不到數字，故直接讀圖。
    """
    import io, base64
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return {"budget":0,"actual":0,"diff":0,"hr_rate":0,"err":"pypdfium2 未安裝"}

    s3 = boto3.client("s3", region_name=REGION)
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)

    try:
        pdf_bytes = s3.get_object(Bucket="s3-education-0912", Key=s3_key)["Body"].read()
    except Exception as e:
        return {"budget":0,"actual":0,"diff":0,"hr_rate":0,"err":f"下載失敗:{e}"}

    pdf = pdfium.PdfDocument(pdf_bytes)

    def page_png_b64(idx, dpi=200):
        bmp = pdf[idx].render(scale=dpi/72)
        buf = io.BytesIO()
        bmp.to_pil().save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode()

    def ask(img_b64, prompt):
        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version":"bedrock-2023-05-31","max_tokens":400,
                "messages":[{"role":"user","content":[
                    {"type":"image","source":{"type":"base64","media_type":"image/png","data":img_b64}},
                    {"type":"text","text":prompt}
                ]}]
            }),
            contentType="application/json", accept="application/json")
        return json.loads(resp["body"].read())["content"][0]["text"].strip()

    READ_PROMPT = (
        "這是台灣非營利幼兒園財務報告的一頁。請找出「收支預算執行情形」或收入/支出明細表，"
        "萃取下列數字（新台幣元，去除逗號）：\n"
        "教保費收入預算數、教保費收入決算數、人事費預算數、人事費決算數。\n"
        "只回傳 JSON：{\"budget\":數,\"actual\":數,\"hr_budget\":數,\"hr_actual\":數}\n"
        "找不到的欄位填 0。此頁無相關表格則回傳全 0。")

    total = len(pdf)
    # 收支表通常集中在前 30 頁，優先掃這些
    found = {"budget":0,"actual":0,"hr_budget":0,"hr_actual":0}
    for idx in range(min(total, 30)):
        try:
            ans = ask(page_png_b64(idx), READ_PROMPT)
            m = re.search(r'\{.*\}', ans, re.DOTALL)
            if not m:
                continue
            d = json.loads(m.group())
            # 累積：一旦某頁湊齊教保費預算+決算與人事費，就採用
            b  = float(d.get("budget",0) or 0)
            a  = float(d.get("actual",0) or 0)
            hb = float(d.get("hr_budget",0) or 0)
            ha = float(d.get("hr_actual",0) or 0)
            # 填補尚未取得的欄位
            if b  and not found["budget"]:    found["budget"]    = b
            if a  and not found["actual"]:    found["actual"]    = a
            if hb and not found["hr_budget"]: found["hr_budget"] = hb
            if ha and not found["hr_actual"]: found["hr_actual"] = ha
            # 四項到齊即可停止
            if all(found.values()):
                break
        except Exception:
            continue

    pdf.close()

    budget  = found["budget"]
    actual  = found["actual"]
    diff    = budget - actual
    hr_rate = (found["hr_actual"] / found["hr_budget"] * 100) if found["hr_budget"] else 0.0

    return {"budget":budget, "actual":actual, "diff":diff,
            "hr_rate":round(hr_rate,2), "err":""}


def extract_financials_from_bytes(pdf_bytes, max_pages=30):
    """
    與 extract_financials_from_pdf 相同的解析邏輯，但輸入是 PDF bytes
    （供第二頁「上傳分析」使用）。
    """
    import io, base64
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return {"budget":0,"actual":0,"diff":0,"hr_rate":0,"err":"pypdfium2 未安裝"}

    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
    except Exception as e:
        return {"budget":0,"actual":0,"diff":0,"hr_rate":0,"err":f"PDF 讀取失敗:{e}"}

    def page_png_b64(idx, dpi=200):
        bmp = pdf[idx].render(scale=dpi/72)
        buf = io.BytesIO()
        bmp.to_pil().save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode()

    def ask(img_b64, prompt):
        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version":"bedrock-2023-05-31","max_tokens":400,
                "messages":[{"role":"user","content":[
                    {"type":"image","source":{"type":"base64","media_type":"image/png","data":img_b64}},
                    {"type":"text","text":prompt}
                ]}]
            }),
            contentType="application/json", accept="application/json")
        return json.loads(resp["body"].read())["content"][0]["text"].strip()

    READ_PROMPT = (
        "這是一份台灣『非營利幼兒園』財務報告的其中一頁（不是國小、不是公立學校）。\n"
        "請做兩件事：\n"
        "1. 找出這份報告的『園所名稱』與『學年度』（例如「安溪非營利幼兒園」「111學年度」）。"
        "通常出現在封面、標題或表頭；找不到就填空字串。\n"
        "2. 找出「收支預算執行情形」或收入/支出明細表，萃取下列數字（新台幣元，去逗號）："
        "教保費收入預算數、教保費收入決算數、人事費預算數、人事費決算數。\n"
        "只回傳 JSON：{\"name\":\"園所名稱\",\"period\":\"XXX學年度\","
        "\"budget\":數,\"actual\":數,\"hr_budget\":數,\"hr_actual\":數}\n"
        "找不到的數字欄位填 0，找不到的文字欄位填空字串。此頁無相關內容則數字全填 0。")

    found = {"budget":0,"actual":0,"hr_budget":0,"hr_actual":0}
    meta  = {"name":"", "period":""}
    for idx in range(min(len(pdf), max_pages)):
        try:
            ans = ask(page_png_b64(idx), READ_PROMPT)
            m = re.search(r'\{.*\}', ans, re.DOTALL)
            if not m:
                continue
            d = json.loads(m.group())
            # 數字欄位
            for k in found:
                v = float(d.get(k,0) or 0)
                if v and not found[k]:
                    found[k] = v
            # 文字欄位（名稱/學年度）：取第一個非空值
            for mk in meta:
                val = str(d.get(mk, "") or "").strip()
                if val and not meta[mk]:
                    meta[mk] = val
            # 數字到齊即可停止（名稱/學年度通常在前幾頁已抓到）
            if all(found.values()):
                break
        except Exception:
            continue
    pdf.close()

    budget  = found["budget"]; actual = found["actual"]
    diff    = budget - actual
    hr_rate = (found["hr_actual"] / found["hr_budget"] * 100) if found["hr_budget"] else 0.0
    return {"budget":budget,"actual":actual,"diff":diff,"hr_rate":round(hr_rate,2),
            "name":meta["name"], "period":meta["period"], "err":""}


def render_analysis(garden_display, period_label, budget, actual, diff, hr_rate,
                    pdf_bytes=None, pdf_filename=None):
    """共用的分析結果渲染：財務卡片 → SageMaker 風險卡 → Bedrock 審計建議 → 下載。
    pdf_bytes/pdf_filename：若提供，額外顯示「下載原始 PDF」按鈕。"""
    st.markdown('<div class="sec-title">💰 關鍵財務特徵</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    def fin_card(col, label, value, fmt="{:,.0f}"):
        col.markdown(
            f'<div class="fin-card"><div class="label">{label}</div>'
            f'<div class="value">{fmt.format(value)}</div></div>',
            unsafe_allow_html=True)
    fin_card(c1, "教保費收入　預算數 (元)", budget)
    fin_card(c2, "教保費收入　決算數 (元)", actual)
    diff_pct = abs(diff)/max(abs(budget),1)*100
    fin_card(c3, f"差異金額 (元)　差異率 {diff_pct:.1f}%", diff)
    fin_card(c4, "人事費執行率", hr_rate, fmt="{:.1f}%")

    # SageMaker 風險
    with st.spinner("呼叫 SageMaker XGBoost 進行風險評分…"):
        risk_level, csv_str = predict_risk(budget, actual, diff, hr_rate)
    st.markdown('<div class="sec-title">🎯 SageMaker 風險評分結果</div>', unsafe_allow_html=True)
    if risk_level is None:
        st.error(f"推論失敗：{csv_str}")
        risk_level = 0
    current = min(risk_level, 3)

    # 四格等級橫排：命中的點亮，其餘變暗
    # 注意：HTML 必須壓成單行、無前導縮排，否則 Streamlit 會誤判為程式碼區塊
    border_colors = {0:"#22c55e", 1:"#eab308", 2:"#f97316", 3:"#ef4444"}
    cells = []
    for lvl in [0, 1, 2, 3]:
        cfg = RISK_CONFIG[lvl]
        active = (lvl == current)
        bcolor = border_colors[lvl]
        cls = "risk-cell-on" if active else "risk-cell-off"
        shadow = f"box-shadow:0 0 18px {bcolor}66;" if active else ""
        en_color = bcolor if active else "#5b6685"
        badge = f'<div class="rc-badge" style="background:{bcolor}">目前等級</div>' if active else ""
        cells.append(
            f'<div class="risk-cell {cls}" style="border-color:{bcolor};{shadow}">'
            f'<div class="rc-icon">{cfg["icon"]}</div>'
            f'<div class="rc-en" style="color:{en_color}">{cfg["en"]}</div>'
            f'<div class="rc-name">{cfg["name"]}</div>'
            f'<div class="rc-action">{cfg["action"]}</div>'
            f'{badge}</div>'
        )
    cards_html = '<div class="risk-grid">' + "".join(cells) + '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
    st.caption(f"風險等級共 4 級（0 低 → 3 極高），本案判定為第 {current} 級。輸入特徵：{csv_str}")

    # 當前等級設定（供後續報告使用）
    rc = RISK_CONFIG[current]

    # 裁罰紀錄查詢（自動）
    render_penalty_section(garden_display)

    # Bedrock 審計建議
    with st.spinner("生成 Bedrock AI 審計建議…"):
        advice = get_audit_advice(garden_display, period_label, budget, actual, diff, hr_rate, risk_level)
    st.markdown('<div class="sec-title">📝 Bedrock AI 審計建議</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="audit-box">{advice.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

    st.markdown("---")
    report = (f"Smart Watchdog 風險評估報告\n園所：{garden_display}\n期間：{period_label}\n"
              f"預算數：{budget:,.0f} 元\n決算數：{actual:,.0f} 元\n差異金額：{diff:,.0f} 元\n"
              f"人事費執行率：{hr_rate:.1f}%\n風險等級：{rc['name']}\n建議處置：{rc['action']}\n\n"
              f"審計建議：\n{advice}\n")

    dl_c1, dl_c2 = st.columns(2)
    with dl_c1:
        st.download_button("📥 下載評估報告 (.txt)", data=report,
            file_name=f"watchdog_{garden_display}_{period_label}.txt",
            mime="text/plain", use_container_width=True)
    with dl_c2:
        if pdf_bytes:
            fname = pdf_filename or f"{garden_display}_{period_label}.pdf"
            if not fname.lower().endswith(".pdf"):
                fname += ".pdf"
            st.download_button("📄 下載原始 PDF", data=pdf_bytes,
                file_name=fname, mime="application/pdf", use_container_width=True)
        else:
            st.button("📄 下載原始 PDF", disabled=True, use_container_width=True,
                      help="此檢視無可用的原始 PDF")

    return current   # 回傳風險等級，供 CSV 快取寫入


def get_history_series(_years_map, garden_display):
    """
    回傳該園所歷年財務數列（供折線圖）。
    每個學年度優先讀 CSV 快取；沒有才以 AI 解析 PDF，並將結果存回 CSV。
    _years_map: {年度字串: s3_key}
    """
    rows = []
    for year in sorted(_years_map.keys()):
        cached = lookup_analysis(year, garden_display)
        if cached:
            b, a, hr = cached["budget"], cached["actual"], cached["hr_rate"]
        else:
            fin = extract_financials_from_pdf(_years_map[year], garden_display, year)
            b  = fin.get("budget", 0) or 0
            a  = fin.get("actual", 0) or 0
            hr = fin.get("hr_rate", 0) or 0
            # 有擷取到數字才存回 CSV
            if any([b, a, hr]):
                d = b - a
                rlvl, _ = predict_risk(b, a, d, hr)
                if rlvl is None:
                    rlvl = 0
                save_analysis_csv(year, garden_display, b, a, hr, rlvl)
        rows.append({
            "學年度": f"{year}",
            "教保費預算數": b,
            "教保費決算數": a,
            "人事費執行率(%)": hr,
        })
    return rows


def render_history_charts(years_map, garden_display):
    """在分析結果上方顯示歷年趨勢折線圖。"""
    import pandas as pd
    st.markdown('<div class="sec-title">📈 歷年財務趨勢</div>', unsafe_allow_html=True)

    if len(years_map) < 1:
        st.info("此園所無可用的歷年資料。")
        return

    with loading(f"正在解析 {len(years_map)} 個學年度的歷年資料…", "逐年辨識財務數字以繪製趨勢圖"):
        rows = get_history_series(years_map, garden_display)

    df = pd.DataFrame(rows).set_index("學年度")

    # 收入（預算 vs 決算）折線圖
    st.caption("教保費收入：預算數 vs 決算數（元）")
    st.line_chart(df[["教保費預算數", "教保費決算數"]], height=260)

    # 人事費執行率折線圖
    st.caption("人事費執行率（%）")
    st.line_chart(df[["人事費執行率(%)"]], height=220)

    with st.expander("查看歷年數據明細"):
        st.dataframe(df, use_container_width=True)


def normalize_period(period_text):
    """從『113學年度』『113 學年度』『113』等取出年度數字字串，回傳 (年度數字, 標準資料夾名)。"""
    m = re.search(r"(\d{2,3})", str(period_text))
    if not m:
        return None, None
    y = m.group(1)
    return y, f"{y}學年度"


def clean_school_name(name):
    """把使用者/PDF 名稱清成純學校名（去掉行政區、機構後綴、編號前綴、空白）。
    例：『新北市安溪非營利幼兒園』→『安溪』"""
    s = str(name).strip()
    s = re.sub(r"^N\d+", "", s)                       # 去掉開頭 N01 之類編號
    for token in ["新北市", "非營利幼兒園", "幼兒園", "非營利",
                  "學年度", "財務報告", "附設", " ", "　"]:
        s = s.replace(token, "")
    return s.strip() or "未命名"


# ── 分析數據 CSV 快取（每學年度一檔，存在 S3）──────────────────────────────
ANALYSIS_BUCKET = "s3-education-0912"
ANALYSIS_PREFIX = "資料集/分析快取/"
ANALYSIS_HEADER = ["編號", "校名", "教保費預算數", "教保費決算數", "人事費執行率", "風險評級"]


def _get_school_code(school):
    """依既有 S3 檔名規則取得該校編號（同校沿用、新校 max+1）。回傳兩位數字串。"""
    import urllib.parse as _up
    s3 = boto3.client("s3", region_name=REGION)
    name_to_code, max_code = {}, 0
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for pg in paginator.paginate(Bucket=ANALYSIS_BUCKET, Prefix="資料集/非營利園財報/"):
            for obj in pg.get("Contents", []):
                fn = _up.unquote(obj["Key"].split("/")[-1]).replace(".pdf", "")
                m = re.match(r"N(\d+)(.+?)_(\d+)學年度", fn)
                if not m:
                    continue
                code, ename = m.group(1), clean_school_name(m.group(2))
                name_to_code.setdefault(ename, code)
                max_code = max(max_code, int(code))
    except Exception:
        pass
    sc = clean_school_name(school)
    return name_to_code.get(sc, f"{max_code + 1:02d}")


def _analysis_csv_key(period_text):
    y, folder = normalize_period(period_text)
    if not folder:
        return None
    return f"{ANALYSIS_PREFIX}{folder}_analysis.csv"


def read_analysis_csv(period_text):
    """讀取該學年度分析 CSV，回傳 {校名: dict}。無檔則回傳空 dict。"""
    import csv, io
    key = _analysis_csv_key(period_text)
    if not key:
        return {}
    s3 = boto3.client("s3", region_name=REGION)
    try:
        body = s3.get_object(Bucket=ANALYSIS_BUCKET, Key=key)["Body"].read().decode("utf-8-sig")
    except Exception:
        return {}
    out = {}
    for row in csv.DictReader(io.StringIO(body)):
        name = (row.get("校名") or "").strip()
        if name:
            out[name] = row
    return out


def lookup_analysis(period_text, garden_display):
    """查該學年度 CSV 是否已有此校資料；有則回傳 dict(budget/actual/hr_rate/risk)，否則 None。"""
    data = read_analysis_csv(period_text)
    name = clean_school_name(garden_display)

    # 比對：先精確、再用去空白正規化容錯
    row = data.get(name)
    if not row:
        def norm(s):
            return re.sub(r"\s|　", "", str(s))
        target = norm(name)
        for k, v in data.items():
            if norm(k) == target:
                row = v
                break
    if not row:
        return None
    try:
        return {
            "budget": float(row.get("教保費預算數") or 0),
            "actual": float(row.get("教保費決算數") or 0),
            "hr_rate": float(row.get("人事費執行率") or 0),
            "risk": int(float(row.get("風險評級") or 0)),
        }
    except ValueError:
        return None


def save_analysis_csv(period_text, garden_display, budget, actual, hr_rate, risk_level):
    """把一筆分析數據寫入（或更新）該學年度 CSV，依學校編號排序。"""
    import csv, io
    key = _analysis_csv_key(period_text)
    if not key:
        return False
    name = clean_school_name(garden_display)
    code = _get_school_code(garden_display)

    data = read_analysis_csv(period_text)   # {校名: row}
    data[name] = {
        "編號": code, "校名": name,
        "教保費預算數": f"{budget:.0f}",
        "教保費決算數": f"{actual:.0f}",
        "人事費執行率": f"{hr_rate:.2f}",
        "風險評級": str(int(risk_level)),
    }

    # 依編號排序後寫回
    rows = sorted(data.values(), key=lambda r: r.get("編號", "99"))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=ANALYSIS_HEADER)
    w.writeheader()
    for r in rows:
        w.writerow({h: r.get(h, "") for h in ANALYSIS_HEADER})

    s3 = boto3.client("s3", region_name=REGION)
    try:
        s3.put_object(Bucket=ANALYSIS_BUCKET, Key=key,
                      Body=buf.getvalue().encode("utf-8-sig"),
                      ContentType="text/csv")
        return True
    except Exception:
        return False


def upload_pdf_to_s3(pdf_bytes, garden_name, period_text):
    """
    依學年度上傳 PDF 至 S3，檔名格式：
      資料集/非營利園財報/{年度}學年度/N{編號}{校名}_{年度}學年度財務報告.pdf
    例：資料集/非營利園財報/113學年度/N01安溪_113學年度財務報告.pdf

    編號規則：
      - 若全庫任何學年度已有同一校名，沿用其既有編號（同校跨年度一致）。
      - 若為新學校，取全庫最大編號 +1。
    重複比對：
      - 若該學年度資料夾內已存在相同校名的檔案（不論編號），不重複上傳。
    回傳 (成功bool, 訊息, s3_uri)
    """
    from botocore.exceptions import ClientError as _ClientError
    BUCKET = "s3-education-0912"
    ROOT   = "資料集/非營利園財報/"

    y, folder = normalize_period(period_text)
    if not y:
        return False, "無法從學年度欄位辨識年度數字，請填入例如『113學年度』", ""

    school = clean_school_name(garden_name)
    s3 = boto3.client("s3", region_name=REGION)

    # 掃描全庫既有檔案，建立 {校名: 編號} 對應，並記錄最大編號
    name_to_code = {}     # 校名 -> "01"
    max_code = 0
    year_school_exists = False   # 該學年度是否已有同校名檔案
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for pg in paginator.paginate(Bucket=BUCKET, Prefix=ROOT):
            for obj in pg.get("Contents", []):
                fname = urllib.parse.unquote(obj["Key"].split("/")[-1])
                m = re.match(r"N(\d+)(.+?)_(\d+)學年度", fname.replace(".pdf", ""))
                if not m:
                    continue
                code, existing_name, existing_year = m.group(1), m.group(2), m.group(3)
                clean_existing = clean_school_name(existing_name)
                name_to_code.setdefault(clean_existing, code)
                max_code = max(max_code, int(code))
                # 該學年度是否已有同校
                if existing_year == y and clean_existing == school:
                    year_school_exists = True
    except Exception as e:
        return False, f"讀取資料庫既有清單失敗：{e}", ""

    # 決定編號：同校沿用，新校 max+1
    if school in name_to_code:
        code = name_to_code[school]
    else:
        code = f"{max_code + 1:02d}"

    prefix = f"{ROOT}{folder}/"
    filename = f"N{code}{school}_{folder}財務報告.pdf"
    key = f"{prefix}{filename}"

    # 重複比對：該學年度已有同校名 → 不上傳
    if year_school_exists:
        return (False,
                f"資料庫在 {folder} 已有「{school}」的財報，未重複上傳。",
                f"s3://{BUCKET}/{prefix}")

    # 精準比對同一個 key（同編號同校名同學年）
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return False, f"資料庫已有相同檔案，未重複上傳：{filename}", f"s3://{BUCKET}/{key}"
    except _ClientError as e:
        if e.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey", "NotFound"):
            return False, f"檢查既有檔案時發生錯誤：{e}", ""

    # 資料夾若不存在先建立標記
    existed = False
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix, MaxKeys=1)
        existed = resp.get("KeyCount", 0) > 0
    except Exception:
        pass
    if not existed:
        try:
            s3.put_object(Bucket=BUCKET, Key=prefix)
        except Exception:
            pass

    try:
        s3.put_object(Bucket=BUCKET, Key=key, Body=pdf_bytes, ContentType="application/pdf")
    except Exception as e:
        return False, f"上傳失敗：{e}", ""

    folder_note = "（已建立新學年度資料夾）" if not existed else ""
    code_note = "（沿用既有編號）" if school in name_to_code else "（新學校，指派新編號）"
    return True, f"上傳成功：{filename} {code_note}{folder_note}", f"s3://{BUCKET}/{key}"

# ── SageMaker 推論 ────────────────────────────────────────────────────────────
def predict_risk(budget, actual, diff, hr_rate):
    rt = boto3.client("sagemaker-runtime", region_name=REGION)
    csv_str = f"{budget},{actual},{diff},{hr_rate}"
    try:
        resp = rt.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="text/csv",
            Body=csv_str,
        )
        raw = resp["Body"].read().decode().strip()
        return int(float(raw)), csv_str
    except Exception as e:
        return None, str(e)

# ── Bedrock 審計建議 ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def get_audit_advice(garden_name, year, budget, actual, diff, hr_rate, risk_level):
    client = boto3.client("bedrock-runtime", region_name=REGION)
    risk_name = RISK_CONFIG.get(risk_level, {}).get("name", "未知")
    prompt = f"""你是一位台灣「非營利幼兒園」財務稽查專家。
注意：以下對象是非營利幼兒園（幼教機構），不是國小、也不是公立學校，請勿誤判機構類型。

分析對象：{garden_name}
期間：{year}
財務摘要：
- 教保費收入預算數：{budget:,.0f} 元
- 教保費收入決算數：{actual:,.0f} 元
- 差異金額：{diff:,.0f} 元（{abs(diff)/max(abs(budget),1)*100:.1f}%）
- 人事費執行率：{hr_rate:.1f}%
- AI 風險評級：{risk_name}

請以繁體中文提供（全程以「非營利幼兒園」的角度撰寫）：
1. 財務狀況摘述（2-3句）
2. 主要風險點分析（條列，2-3點）
3. 具體審計建議（條列，2-3點）

語氣專業但易懂，使用 📊 💡 ⚠️ ✅ 等表情符號增加可讀性。"""
    try:
        resp = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version":"bedrock-2023-05-31",
                "max_tokens":600,
                "messages":[{"role":"user","content":prompt}]
            }),
            contentType="application/json", accept="application/json"
        )
        return json.loads(resp["body"].read())["content"][0]["text"].strip()
    except Exception as e:
        return f"審計建議生成失敗：{e}"


# ── 裁罰紀錄查詢（全國教保資訊網）──────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def query_penalty(school_name, city="新北市"):
    """
    查詢幼兒園裁罰紀錄，回傳 list[dict]（空 list = 查無紀錄）。
    資料來源：全國教保資訊網 punishSearch.aspx。
    此系統僅收錄「有裁罰紀錄」的幼兒園。
    """
    import requests, urllib3
    from bs4 import BeautifulSoup
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    SEARCH_URL = "https://ap.ece.moe.edu.tw/webecems/punishSearch.aspx"
    VIEW_BASE  = "https://ap.ece.moe.edu.tw/webecems/dtl/punish_view.aspx?sch="
    CITY_CODES = {
        "基隆市":"01","臺北市":"02","台北市":"02","新北市":"03","桃園市":"05",
        "新竹市":"06","新竹縣":"07","苗栗縣":"08","臺中市":"09","台中市":"09",
        "彰化縣":"11","南投縣":"12","雲林縣":"13","嘉義市":"14","嘉義縣":"15",
        "臺南市":"16","台南市":"16","高雄市":"18","屏東縣":"20","臺東縣":"21",
        "台東縣":"21","花蓮縣":"22","宜蘭縣":"04","澎湖縣":"23","金門縣":"24","連江縣":"25",
    }

    def _hidden(soup, name):
        el = soup.find("input", {"name": name})
        return el["value"] if el and el.has_attr("value") else ""

    sess = requests.Session()
    sess.headers.update({"User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")})

    # 網路請求包在 try 內；失敗回傳標記（會被 cache，避免每次 rerun 重試逾時）
    try:
        r = sess.get(SEARCH_URL, verify=False, timeout=3)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        payload = {
            "__VIEWSTATE": _hidden(soup, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": _hidden(soup, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": _hidden(soup, "__EVENTVALIDATION"),
            "ddlKey": "school_name",
            "txtKeyNameS": school_name,
            "ddlCityS": CITY_CODES.get((city or "").strip(), ""),
            "ddlAreaS": "",
            "btnSearch": "搜尋",
        }
        r2 = sess.post(SEARCH_URL, data=payload, verify=False, timeout=3)
        r2.raise_for_status()
        r2.encoding = "utf-8"
    except Exception as e:
        # 常見於雲端主機無法連外部政府網站（逾時/被擋）
        return {"ok": False, "results": [], "error": str(e)}

    soup2 = BeautifulSoup(r2.text, "html.parser")
    results = []
    for span in soup2.find_all("span", id=lambda x: x and "lblSchName" in x):
        idx = span.get("id").split("_")[-1]
        def field(key):
            el = soup2.find("span", id=f"GridView1_{key}_{idx}")
            return el.get_text(strip=True) if el else ""
        detail_url = None
        view_link = soup2.find("a", id=f"GridView1_lbView_{idx}")
        if view_link and view_link.has_attr("onclick"):
            m = re.search(r"punish_view\.aspx\?sch=([A-Za-z0-9+/=]+)", view_link["onclick"])
            if m:
                detail_url = VIEW_BASE + m.group(1)
        results.append({
            "school": span.get_text(strip=True),
            "city": field("lblCity"), "area": field("lblArea"),
            "public": field("lblPub"), "tel": field("lblTel"),
            "capacity": field("lblGenStd"), "status": field("lblBStatus"),
            "detail_url": detail_url,
        })
    return {"ok": True, "results": results, "error": ""}


def render_penalty_section(garden_display):
    """在分析結果中顯示該園所的裁罰紀錄查詢結果。"""
    st.markdown('<div class="sec-title">⚖️ 裁罰紀錄查詢（全國教保資訊網）</div>', unsafe_allow_html=True)

    # 用純校名查詢（去掉行政區/機構後綴，提高命中率）
    keyword = clean_school_name(garden_display)
    with loading("正在查詢裁罰紀錄…", f"向全國教保資訊網查詢「{keyword}」"):
        resp = query_penalty(keyword, city="新北市")

    # 查詢失敗（多為雲端主機無法連外部政府網站）
    if not resp.get("ok"):
        st.info("裁罰紀錄查詢暫時無法連線至全國教保資訊網（伺服器對外連線受限）。")
        st.markdown("可自行至 [全國教保資訊網 - 裁罰紀錄查詢]"
                    "(https://ap.ece.moe.edu.tw/webecems/punishSearch.aspx) 查詢。")
        return

    results = resp.get("results", [])
    if not results:
        st.success(f"✅ 查無裁罰紀錄：以關鍵字「{keyword}」在全國教保資訊網查詢，未發現裁罰紀錄。")
        st.caption("此系統僅收錄有裁罰紀錄的幼兒園；查不到通常代表無裁罰紀錄。")
        return

    st.error(f"⚠️ 發現 {len(results)} 筆裁罰紀錄（關鍵字「{keyword}」）")
    for i, r in enumerate(results, 1):
        lines = [
            f"**[{i}] {r['school']}**",
            f"- 縣市鄉鎮：{r['city']} {r['area']}",
            f"- 設立別：{r['public']}　電話：{r['tel']}",
            f"- 核定人數：{r['capacity']}　營運狀態：{r['status']}",
        ]
        if r.get("detail_url"):
            lines.append(f"- 裁罰明細：[開啟連結]({r['detail_url']})")
        st.markdown("\n".join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# 主畫面
# ══════════════════════════════════════════════════════════════════════════════

# 標題列
# 標題列
st.markdown("""
<div class="main-header">
  <h1>🛡️ 新北市教育局 - 小小守護員 Smart Watchdog</h1>
  <p>智慧風險預警管理系統 ｜ Powered by Amazon SageMaker</p>
</div>
""", unsafe_allow_html=True)

# ── 左側選單：頁面切換 ────────────────────────────────────────────────────────
# 若有待跳轉旗標，在 radio 建立「之前」注入（避開 Streamlit 限制）
if "pending_nav" in st.session_state:
    st.session_state["nav_page"] = st.session_state.pop("pending_nav")

with st.sidebar:
    st.markdown('<div class="menu-title">📑 功能選單</div>', unsafe_allow_html=True)
    page = st.radio(
        "選擇功能頁面",
        options=["🔍 園所查詢", "📤 上傳分析", "⚡ 一鍵分析所有資料"],
        label_visibility="collapsed",
        key="nav_page",
    )
    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# 第一頁：園所查詢
# ══════════════════════════════════════════════════════════════════════════════
if page == "🔍 園所查詢":
    with st.sidebar:
        st.markdown('<div class="sidebar-label">🔍 幼兒園搜尋器</div>', unsafe_allow_html=True)

        with st.spinner("載入園所清單…"):
            gardens = load_kindergarten_list()

        garden_keys = sorted(gardens.keys())

        # ── 模糊搜尋（正規化 + 相似度排序）─────────────────────────────────
        import difflib
        def normalize(s):
            s = s.upper()
            for token in ["非營利幼兒園", "幼兒園", "非營利", "學年度", "財務報告", " "]:
                s = s.replace(token.upper(), "")
            s = re.sub(r"^N\d+", "", s)
            return s.strip()

        search = st.text_input("輸入園所名稱關鍵字後按下Enter搜尋", placeholder="例：安溪、北大、鷺江…")
        if search:
            q = normalize(search)
            scored = []
            for k in garden_keys:
                cand = normalize(k + gardens[k]["name"])
                if q in cand:
                    score = 1.0
                else:
                    score = difflib.SequenceMatcher(None, q, cand).ratio()
                    if any(ch in cand for ch in q):
                        score = max(score, 0.4)
                scored.append((score, k))
            scored.sort(key=lambda x: -x[0])
            filtered = [k for s, k in scored if s >= 0.3]
            if not filtered:
                filtered = [k for s, k in scored[:10]]
        else:
            filtered = garden_keys

        selected_key = st.selectbox(
            "選擇幼兒園（依相符度排序）",
            options=filtered if filtered else garden_keys,
            format_func=lambda k: f"{k}",
        )

        if selected_key:
            years = sorted(gardens[selected_key]["years"].keys(), reverse=True)
            selected_year = st.selectbox("選擇學年度", options=years, format_func=lambda y: f"{y} 學年度")

        st.markdown("---")
        run_btn = st.button("🚀 開始分析", use_container_width=True, type="primary")

    # 按下「開始分析」→ 記錄選定目標到 session_state（與顯示解耦）
    if run_btn:
        st.session_state["query_target"] = {
            "key": selected_key, "year": selected_year,
        }

    # 主內容：只要有選定目標就顯示（下載按鈕觸發 rerun 後也能持續顯示）
    target = st.session_state.get("query_target")
    # 若目前選擇已變動且尚未重新按分析，仍沿用上次目標
    if not target:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("已收錄園所", f"{len(gardens)} 所")
        with col2:
            st.metric("覆蓋學年度", "110 – 113")
        st.info("👈 從左側選擇幼兒園與學年度，點擊「開始分析」以取得風險評估報告。")
    else:
        t_key  = target["key"]
        t_year = target["year"]
        # 防呆：若該 key 已不存在（清單更新），回到初始畫面
        if t_key not in gardens or t_year not in gardens[t_key]["years"]:
            st.session_state.pop("query_target", None)
            st.info("👈 請重新選擇幼兒園與學年度，點擊「開始分析」。")
        else:
            garden_info = gardens[t_key]
            garden_display = garden_info["name"]
            s3_key = garden_info["years"][t_year]

            st.markdown(f'<div class="sec-title">📋 分析對象：{garden_display} ｜ {t_year} 學年度</div>', unsafe_allow_html=True)

            # 先查該學年度 CSV 快取；有資料就直接用，免跑 AI
            cached = lookup_analysis(t_year, garden_display)
            if cached:
                st.success("⚡ 已從分析資料庫（CSV）快速載入此園所數據，無需重新以 AI 解析。")
                budget  = cached["budget"]
                actual  = cached["actual"]
                hr_rate = cached["hr_rate"]
                diff    = budget - actual
                need_save = False
            else:
                with loading("正在以 AI 視覺解析財務報告 PDF…", "下載並辨識表格數字，約 20-40 秒"):
                    fin = extract_financials_from_pdf(s3_key, garden_display, t_year)
                budget  = fin.get("budget", 0)
                actual  = fin.get("actual", 0)
                diff    = fin.get("diff", 0)
                hr_rate = fin.get("hr_rate", 0)
                need_save = True

                if fin.get("err"):
                    st.warning(f"PDF 解析提示：{fin['err']}")
                if not any([budget, actual, hr_rate]):
                    st.warning("⚠️ 此份報告未能自動擷取到明確財務數字（可能表格格式特殊），以下風險評分僅供參考。")

            # 歷年趨勢折線圖（在 AI 分析結果上方）
            render_history_charts(garden_info["years"], garden_display)

            orig_pdf = fetch_pdf_bytes(s3_key)
            orig_fname = __import__("urllib").parse.unquote(s3_key.split("/")[-1])
            risk_lvl = render_analysis(garden_display, f"{t_year} 學年度", budget, actual, diff, hr_rate,
                                       pdf_bytes=orig_pdf, pdf_filename=orig_fname)

            # 若這次是 AI 新解析（非 CSV 快取），把結果寫入分析 CSV 供日後快速查詢
            if need_save and any([budget, actual, hr_rate]):
                if save_analysis_csv(t_year, garden_display, budget, actual, hr_rate, risk_lvl):
                    st.caption("📝 本次分析數據已存入分析資料庫（CSV），下次查詢將直接載入。")

# ══════════════════════════════════════════════════════════════════════════════
# 第二頁：上傳分析
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📤 上傳分析":
    with st.sidebar:
        st.markdown('<div class="sidebar-label">📤 上傳財報 PDF</div>', unsafe_allow_html=True)
        st.caption("上傳任一份幼兒園財務報告 PDF，系統將自動以 AI 解析並評分。")

    st.markdown('<div class="sec-title">📤 上傳新的財務報告 PDF 進行分析</div>', unsafe_allow_html=True)
    st.write("支援掃描或文字型 PDF。系統會用 Claude 視覺模型讀取表格，擷取教保費收入與人事費的預算/決算，再交由 SageMaker 評估風險等級。")

    # pending_* 用於在 widget 建立「之前」注入回填值（避開 Streamlit 限制）
    if "pending_name" in st.session_state:
        st.session_state["up_name_input"] = st.session_state.pop("pending_name")
    if "pending_period" in st.session_state:
        st.session_state["up_period_input"] = st.session_state.pop("pending_period")

    uploaded = st.file_uploader("拖曳或選擇 PDF 檔案", type=["pdf"])
    up_name  = st.text_input("園所名稱（用於報告與審計建議，可留空由系統自動判讀）",
                             placeholder="例：安溪非營利幼兒園", key="up_name_input")
    up_period = st.text_input("期間 / 學年度（可留空由系統自動判讀）",
                              placeholder="例：111 學年度", key="up_period_input")

    up_run = st.button("🚀 開始分析上傳的 PDF", type="primary", use_container_width=True,
                       disabled=(uploaded is None))

    # 觸發分析：解析 → 存進 session_state → 排程回填 → rerun
    if uploaded is not None and up_run:
        pdf_bytes = uploaded.read()
        with loading("正在以 AI 視覺解析上傳的 PDF…", "判讀園所名稱、學年度與財務數字，約 20-60 秒"):
            fin = extract_financials_from_bytes(pdf_bytes)

        pdf_name   = fin.get("name", "").strip()
        pdf_period = fin.get("period", "").strip()
        user_name   = (up_name or "").strip()
        user_period = (up_period or "").strip()

        gname  = user_name   or pdf_name   or uploaded.name.replace(".pdf", "")
        period = user_period or pdf_period or "（未標示學年度）"

        # 排程把判讀值回填到輸入框（在下次 rerun、widget 建立前注入）
        if not user_name and pdf_name:
            st.session_state["pending_name"] = pdf_name
        if not user_period and pdf_period:
            st.session_state["pending_period"] = pdf_period

        # 把結果存進 session_state，顯示邏輯與按鈕解耦，rerun 後仍可顯示
        import base64 as _b64
        st.session_state["last_result"] = {
            "file": uploaded.name, "size_kb": len(pdf_bytes)/1024,
            "gname": gname, "period": period,
            "budget": fin.get("budget",0), "actual": fin.get("actual",0),
            "diff": fin.get("diff",0), "hr_rate": fin.get("hr_rate",0),
            "err": fin.get("err",""),
            "auto_name": pdf_name if (not user_name and pdf_name) else "",
            "auto_period": pdf_period if (not user_period and pdf_period) else "",
            "pdf_b64": _b64.b64encode(pdf_bytes).decode(),  # 保留原始 PDF 供上傳
        }
        # 新分析 → 重置上傳確認狀態
        st.session_state.pop("show_upload_form", None)
        st.session_state.pop("upload_done", None)
        st.rerun()

    # 顯示最近一次分析結果（不綁按鈕，rerun 後也能持續顯示）
    res = st.session_state.get("last_result")
    if res:
        st.markdown(f'<div class="sec-title">📋 分析對象：{res["file"]}（{res["size_kb"]:,.0f} KB）</div>', unsafe_allow_html=True)
        auto = [x for x in [
            f"園所名稱：{res['auto_name']}" if res['auto_name'] else "",
            f"學年度：{res['auto_period']}" if res['auto_period'] else "",
        ] if x]
        if auto:
            st.success("✅ 已自動從 PDF 判讀並填入：" + "；".join(auto))
        if res.get("err"):
            st.warning(f"PDF 解析提示：{res['err']}")
        if not any([res["budget"], res["actual"], res["hr_rate"]]):
            st.warning("⚠️ 未能從此 PDF 擷取到明確財務數字（可能非收支預決算報表或表格格式特殊），以下風險評分僅供參考。")
        import base64 as _b64r
        _orig = _b64r.b64decode(res["pdf_b64"]) if res.get("pdf_b64") else None
        render_analysis(res["gname"], res["period"], res["budget"], res["actual"], res["diff"], res["hr_rate"],
                        pdf_bytes=_orig, pdf_filename=res.get("file"))

        # ── 上傳至資料庫 ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="sec-title">🗄️ 存檔管理</div>', unsafe_allow_html=True)

        if st.session_state.get("upload_done"):
            done = st.session_state["upload_done"]
            if done.get("ok"):
                st.success(f"✅ {done['msg']}")
                st.markdown(f"S3 路徑：`{done['uri']}`")
            elif "已有相同" in done.get("msg", ""):
                st.warning(f"⚠️ {done['msg']}")
                if done.get("uri"):
                    st.markdown(f"既有檔案：`{done['uri']}`")
            else:
                st.error(f"❌ {done['msg']}")
        elif not st.session_state.get("show_upload_form"):
            if st.button("🗄️ 上傳至資料庫", use_container_width=True):
                st.session_state["show_upload_form"] = True
                st.rerun()
        else:
            st.info("請確認以下資訊無誤，確認後將依學年度存入資料庫。")
            db_name = st.text_input("學校 / 園所名稱", value=res["gname"], key="db_name")
            db_period = st.text_input("學年度（例：113學年度）", value=res["period"], key="db_period")

            y_preview, folder_preview = normalize_period(db_period)
            if folder_preview:
                st.caption(f"將存入資料夾：資料集/非營利園財報/{folder_preview}/")
            else:
                st.caption("⚠️ 目前學年度格式無法辨識年度數字，請輸入含數字的學年度")

            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("✖ 取消", use_container_width=True):
                    st.session_state.pop("show_upload_form", None)
                    st.rerun()
            with cc2:
                if st.button("✔ 確認無誤，上傳", type="primary", use_container_width=True):
                    import base64 as _b64
                    pdf_bytes = _b64.b64decode(res["pdf_b64"])
                    with loading("正在上傳至資料庫…", "比對重複並寫入 S3 對應學年度資料夾"):
                        ok, msg, uri = upload_pdf_to_s3(pdf_bytes, db_name, db_period)
                    st.session_state["upload_done"] = {"ok": ok, "msg": msg, "uri": uri}
                    st.session_state.pop("show_upload_form", None)
                    # 上傳成功後：清快取 + 將分析數據寫入該學年度 CSV
                    if ok:
                        load_kindergarten_list.clear()
                        b = res.get("budget", 0); a = res.get("actual", 0)
                        hr = res.get("hr_rate", 0)
                        d = res.get("diff", b - a)
                        rlvl, _ = predict_risk(b, a, d, hr)
                        if rlvl is None:
                            rlvl = 0
                        save_analysis_csv(db_period, db_name, b, a, hr, rlvl)
                    st.rerun()
    elif uploaded is None:
        st.info("👈 請於上方選擇一份 PDF 檔案後，點擊「開始分析」。")


# ══════════════════════════════════════════════════════════════════════════════
# 第三頁：一鍵分析所有資料
# ══════════════════════════════════════════════════════════════════════════════
else:
    with st.sidebar:
        st.markdown('<div class="sidebar-label">⚡ 一鍵分析所有資料</div>', unsafe_allow_html=True)
        st.caption("掃描所有園所與學年度，優先讀取 CSV 快取，缺漏才以 AI 分析，"
                   "並依風險等級分區顯示。")

    with st.spinner("載入園所清單…"):
        gardens_all = load_kindergarten_list()

    # 選擇要分析的學年度（預設全部）
    all_years = sorted({y for g in gardens_all.values() for y in g["years"].keys()})
    with st.sidebar:
        pick_year = st.selectbox("選擇學年度（單選）",
                                 options=all_years,
                                 index=len(all_years) - 1 if all_years else 0,
                                 format_func=lambda y: f"{y} 學年度")
        pick_years = [pick_year] if pick_year else []
        only_cache = st.checkbox("僅使用現有 CSV 快取（不呼叫 AI，最快）", value=False)
        run_all = st.button("⚡ 開始一鍵分析", type="primary", use_container_width=True)

    st.markdown('<div class="sec-title">⚡ 一鍵分析所有資料</div>', unsafe_allow_html=True)

    # 建立所有 (校key, 校顯示名, 年度, s3_key) 工作清單
    tasks = []
    for gkey, ginfo in gardens_all.items():
        for yr, s3k in ginfo["years"].items():
            if yr in pick_years:
                tasks.append((gkey, ginfo["name"], yr, s3k))

    if run_all:
        # 先讀各學年度 CSV 快取（減少重複讀取）
        csv_cache = {yr: read_analysis_csv(yr) for yr in pick_years}

        results = []       # 每筆: {key, display, year, budget, actual, hr_rate, risk}
        total = len(tasks)
        done = 0
        prog = st.progress(0.0, text=f"準備分析 {total} 筆資料…")
        status = st.empty()

        for gkey, gdisp, yr, s3k in tasks:
            done += 1
            sc = clean_school_name(gdisp)
            row = csv_cache.get(yr, {}).get(sc)

            if row:
                # 由 CSV 快取取得
                try:
                    b = float(row.get("教保費預算數") or 0)
                    a = float(row.get("教保費決算數") or 0)
                    hr = float(row.get("人事費執行率") or 0)
                    rk = int(float(row.get("風險評級") or 0))
                    src = "快取"
                except ValueError:
                    row = None

            if not row:
                if only_cache:
                    status.caption(f"（{done}/{total}）略過（無快取）：{gdisp} {yr}學年度")
                    prog.progress(done/total, text=f"已處理 {done}/{total}")
                    continue
                # 以 AI 分析
                status.caption(f"（{done}/{total}）AI 分析中：{gdisp} {yr}學年度…")
                fin = extract_financials_from_pdf(s3k, gdisp, yr)
                b = fin.get("budget", 0); a = fin.get("actual", 0)
                hr = fin.get("hr_rate", 0); d = b - a
                rk, _ = predict_risk(b, a, d, hr)
                if rk is None:
                    rk = 0
                # 寫入 CSV
                if any([b, a, hr]):
                    save_analysis_csv(yr, gdisp, b, a, hr, rk)
                src = "AI"

            results.append({
                "key": gkey, "display": gdisp, "year": yr,
                "budget": b, "actual": a, "hr_rate": hr, "risk": min(int(rk), 3),
                "src": src,
            })
            prog.progress(done/total, text=f"已處理 {done}/{total}（{src}）")

        prog.progress(1.0, text=f"完成！共 {len(results)} 筆")
        status.empty()
        st.session_state["batch_results"] = results

    # 顯示批次結果（四區分類）
    results = st.session_state.get("batch_results")
    if not results:
        st.info("👈 於左側選擇學年度後，點「⚡ 開始一鍵分析」。"
                "系統會優先讀取 CSV 快取，缺漏的才以 AI 分析並存回 CSV。")
    else:
        # 統計
        from collections import Counter
        dist = Counter(r["risk"] for r in results)
        c0, c1, c2, c3 = st.columns(4)
        c0.metric("🟢 低風險", dist.get(0, 0))
        c1.metric("🟡 注意風險", dist.get(1, 0))
        c2.metric("🟠 高風險", dist.get(2, 0))
        c3.metric("🔴 極高風險", dist.get(3, 0))
        st.caption(f"共 {len(results)} 筆（點擊任一學校可跳轉檢視完整分析）")

        st.markdown("---")
        cols = st.columns(4)
        headers = {
            0: ("🟢 低風險 Safe", "#22c55e"),
            1: ("🟡 注意風險 Warning", "#eab308"),
            2: ("🟠 高風險 Alert", "#f97316"),
            3: ("🔴 極高風險 Critical", "#ef4444"),
        }
        for lvl in [0, 1, 2, 3]:
            with cols[lvl]:
                title, color = headers[lvl]
                st.markdown(
                    f'<div style="border-top:4px solid {color};background:#111b35;'
                    f'border-radius:10px;padding:10px 12px;margin-bottom:8px;'
                    f'font-weight:700;color:{color}">{title}</div>',
                    unsafe_allow_html=True)
                items = [r for r in results if r["risk"] == lvl]
                items.sort(key=lambda r: (r["display"], r["year"]))
                if not items:
                    st.caption("（無）")
                for r in items:
                    label = f"{clean_school_name(r['display'])}　{r['year']}學年度"
                    if st.button(label, key=f"batch_{r['key']}_{r['year']}",
                                 use_container_width=True):
                        # 點擊 → 設定查詢目標，並用 pending_nav 於下次 rerun（widget 建立前）切頁
                        st.session_state["query_target"] = {"key": r["key"], "year": r["year"]}
                        st.session_state["pending_nav"] = "🔍 園所查詢"
                        st.rerun()
