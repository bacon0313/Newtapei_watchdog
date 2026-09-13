# 實作任務 — 財務風險預警儀表板

- [x] 1. 建立 .venv 環境並安裝 boto3、streamlit、pypdfium2、beautifulsoup4
- [x] 2. 從 Bedrock KB / PDF 擷取財務數據，產出 train.csv
- [x] 3. 建立 IAM 角色、以 SageMaker 內建 XGBoost 訓練 4 級風險模型
- [x] 4. 部署 SageMaker 即時 Endpoint 並驗證推論
- [x] 5. 撰寫 Streamlit app.py
  - [x] 5.1 園所查詢頁（模糊搜尋、財務卡片、歷年趨勢、風險四格、審計建議）
  - [x] 5.2 上傳分析頁（AI 判讀名稱/學年度、自動回填、上傳 S3、重複比對）
  - [x] 5.3 一鍵分析頁（批次、進度顯示、四級分區、點選跳轉）
- [x] 6. 整合全國教保資訊網裁罰紀錄查詢
- [x] 7. 分析結果 CSV 快取層（讀取優先、缺漏才跑 AI、寫回）
- [x] 8. 固定深色主題，修正深色瀏覽器下文字對比
- [x] 9. 部署至 EC2（systemd 常駐、port 8501）
- [ ] 10. （可選）以 Security Group 限制對外來源 IP
