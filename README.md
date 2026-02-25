# LINE 購物單 PDF 生成器

自動生成購物單 PDF 並透過 LINE Bot 傳送。

## 功能特色

- 📊 查詢最新 10 筆訂單資料
- 🖼️ 自動下載並嵌入商品圖片
- 📄 生成精美的 PDF 報表
- 🔗 透過 LINE 傳送下載連結

## 技術棧

- FastAPI
- Playwright (PDF 生成)
- Supabase (資料庫 & 儲存)
- LINE Messaging API
- Pillow (圖片處理)

## 環境變數

需要在 Railway 或 `.env` 設定以下變數：

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
LINE_CHANNEL_SECRET=your_line_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
GOOGLE_CREDENTIALS_FILE=google-credentials.json
GOOGLE_DRIVE_FOLDER_ID=optional_folder_id
```

## 部署到 Railway

1. 將程式碼推送到 GitHub
2. 在 Railway 建立新專案並連接 GitHub
3. 設定環境變數
4. Railway 會自動部署

## 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝 Playwright 瀏覽器
playwright install chromium

# 啟動服務
uvicorn main:app --reload
```

## LINE Webhook 設定

部署後，將 Railway URL 設定到 LINE Developers Console：

```
https://your-app.railway.app/line/webhook
```
