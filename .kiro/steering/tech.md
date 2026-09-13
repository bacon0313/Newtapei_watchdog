# 技術架構

## 前端 / 應用層
- **Streamlit**（`app.py`）：單檔 Web 應用，固定深色主題（`.streamlit/config.toml`）。
- 部署於 **AWS EC2**（Amazon Linux 2023），以 systemd service 常駐執行，對外 port 8501。

## AWS 服務
- **Amazon S3**：存放財報 PDF（`資料集/非營利園財報/{年度}學年度/`）與分析快取 CSV
  （`資料集/分析快取/{年度}學年度_analysis.csv`）。
- **Amazon Bedrock**：
  - Claude（視覺模型）解析掃描版 PDF 表格，擷取財務數字與園所名稱/學年度。
  - Knowledge Base 檢索（輔助）。
  - 產生白話審計建議。
- **Amazon SageMaker**：內建 XGBoost 訓練多分類模型（4 級風險），部署為即時 Endpoint。

## 資料流
PDF（S3）→ Claude 視覺解析財務數字 → SageMaker XGBoost 風險評分
→ Bedrock 審計建議 → 結果寫入 CSV 快取（下次查詢優先讀取，免重跑 AI）。

## 外部資料
- 全國教保資訊網裁罰紀錄查詢（`punish_query.py` 的邏輯，整合進 app）。

## 效能設計
- 分析結果以 S3 CSV 持久化快取，依學校編號索引；查詢時先讀 CSV，缺漏才呼叫 AI。
- Streamlit `st.cache_data` 快取園所清單、PDF 下載等。
