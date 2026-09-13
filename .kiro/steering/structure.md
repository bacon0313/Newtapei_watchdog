# 專案結構

## 上傳至公開儲存庫的檔案
- `app.py` — Streamlit 主應用（園所查詢 / 上傳分析 / 一鍵分析三頁）。
- `punish_query.py` — 全國教保資訊網裁罰紀錄查詢工具。
- `.streamlit/config.toml` — Streamlit 主題設定（固定深色）。
- `architecture.html` / `index.html` — 系統架構 / 說明頁。
- `.kiro/` — Kiro steering、specs、hooks（比賽規則要求保留）。
- `README.md` — 專案說明。

## 刻意排除（見 .gitignore）
- `.venv/`、`__pycache__/` — 虛擬環境與快取。
- 憑證相關：`_creds.ps1`、`_load_creds.py`、`aws_result.txt`。
- 一次性部署 / 除錯 / 探索腳本（含 EC2 instance ID、IP、帳號 ID 等內部資訊）。
- 執行輸出檔（`*_out.txt`、`*_err.txt`、`*.txt`）。
- `train.csv` — 訓練用財務資料，不公開。

## 命名慣例
- S3 財報檔名：`N{兩位編號}{校名}_{年度}學年度財務報告.pdf`（同校跨年度沿用同編號）。
- 分析快取 CSV：`{年度}學年度_analysis.csv`，欄位＝編號,校名,教保費預算數,決算數,人事費執行率,風險評級。
