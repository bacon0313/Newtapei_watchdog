# 🛡️ 小小守護員 Smart Watchdog

新北市教育局 — 非營利幼兒園財務風險預警管理系統。

以 AI 協助教育局快速判讀幼兒園財務報告，找出財務異常、及早介入輔導。

## 功能
- **園所查詢**：選園所與學年度，顯示關鍵財務數字、歷年趨勢、四級風險評分、AI 審計建議、裁罰紀錄。
- **上傳分析**：上傳財報 PDF，AI 自動判讀名稱/學年度/財務數字，評分後存回資料庫。
- **一鍵分析所有資料**：批次分析，依風險等級分區顯示。

## 技術架構
- 前端：Streamlit（`app.py`），部署於 AWS EC2。
- AWS：S3（財報 / 快取）、視覺解析 PDF、審計建議、
  SageMaker XGBoost（4 級風險評分 Endpoint）。
- 外部：全國教保資訊網裁罰紀錄查詢。

## 執行
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install streamlit boto3 pypdfium2 pillow beautifulsoup4 requests
streamlit run app.py
```
需具備可存取上述 AWS 服務的憑證（透過環境變數或 `~/.aws/credentials`，請勿提交至版本庫）。

## 風險等級
| 等級 | 名稱 | 建議處置 |
|---|---|---|
| 0 | 低風險 Safe | 例行監測 |
| 1 | 注意風險 Warning | 持續追蹤 |
| 2 | 高風險 Alert | 加強查核 |
| 3 | 極高風險 Critical | 優先稽查 |

## 安全性
本專案不含任何 AWS 憑證或機密；相關檔案已由 `.gitignore` 排除。

## Kiro 使用
`.kiro/` 內含本專案的 steering（產品/技術/結構規範）、spec（需求/設計/任務）、hook（存檔語法檢查）。
