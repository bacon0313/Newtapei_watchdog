# 設計文件 — 財務風險預警儀表板

## 架構概觀
Streamlit 單頁應用（三個功能頁），部署於 EC2；後端依賴 S3 / Bedrock / SageMaker。

```
使用者 ─▶ Streamlit (EC2:8501)
                │
     ┌──────────┼───────────────┬────────────────┐
     ▼          ▼               ▼                ▼
   S3(PDF)   Bedrock Claude   SageMaker        S3(CSV 快取)
              (視覺解析)      XGBoost Endpoint  (分析結果)
```

## 核心元件（app.py）
- `load_kindergarten_list()`：掃 S3 檔名 → 建立園所清單（含各學年度）。
- `extract_financials_from_pdf() / _from_bytes()`：Claude 視覺解析財務數字。
- `predict_risk()`：呼叫 SageMaker Endpoint 取得 0–3 風險等級。
- `get_audit_advice()`：Bedrock 產生白話審計建議（含快取）。
- `query_penalty()`：查全國教保資訊網裁罰紀錄（timeout 3 秒、失敗回傳標記並快取）。
- CSV 快取層：`read_analysis_csv / lookup_analysis / save_analysis_csv`。
- `upload_pdf_to_s3()`：依學年度上傳、自動建資料夾、重複比對、指派學校編號。

## 風險判定
SageMaker XGBoost 多分類（`objective=multi:softmax`, `num_class=4`），
輸入 4 特徵：預算數、決算數、差異、人事費執行率。

## 快取策略
分析結果寫入 S3 CSV（依學校編號索引）。查詢/趨勢圖/批次分析皆先讀 CSV，
命中則不呼叫 AI，大幅降低延遲與成本。

## 主題與可讀性
`.streamlit/config.toml` 固定深色主題，避免瀏覽器深/淺色偏好造成文字對比不足。
