# LINE PDF Generator - 本地開發模式

## 當前配置
- ✅ 使用 Google Drive 儲存 PDF
- ✅ 使用 ngrok 提供公開網址
- ✅ Base64 圖片嵌入（避免載入問題）
- ✅ 限制 10 筆資料（控制檔案大小）

## 啟動步驟

### 1. 啟動 FastAPI 服務器
```bash
cd /Users/hsiehjiapei/Desktop/line_pdf
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 啟動 ngrok（新終端）
```bash
ngrok http 8000
```

### 3. 更新 LINE Webhook URL
1. 複製 ngrok 提供的 HTTPS 網址（例如：`https://xxxx.ngrok.io`）
2. 前往 [LINE Developers Console](https://developers.line.biz/console/)
3. 選擇你的 Channel → Messaging API
4. 更新 Webhook URL 為：`https://xxxx.ngrok.io/line/webhook`
5. 點擊 **Verify** 測試連接
6. 確保 **Use webhook** 開關是開啟的

## 環境變數（.env）
```
SUPABASE_URL=你的Supabase網址
SUPABASE_SERVICE_ROLE_KEY=你的Supabase金鑰
LINE_CHANNEL_SECRET=你的LINE密鑰
LINE_CHANNEL_ACCESS_TOKEN=你的LINE存取權杖
GOOGLE_CREDENTIALS_FILE=google-credentials.json
GOOGLE_DRIVE_FOLDER_ID=你的Google Drive資料夾ID
```

## Google Drive 設定
請參考 `GOOGLE_DRIVE_SETUP.md` 文件

## 功能說明
- 從 `order_items` 表查詢最新 10 筆訂單
- 從 `product_images_2` 表查詢產品圖片
- 圖片壓縮為 80x80 並轉成 Base64 嵌入 PDF
- PDF 上傳到 Google Drive
- 回傳 Google Drive 分享連結給 LINE 用戶

## 檔案結構
```
line_pdf/
├── main.py                    # 主程式
├── requirements.txt           # Python 依賴
├── .env                       # 環境變數（不提交到 Git）
├── google-credentials.json    # Google 服務帳號憑證（不提交到 Git）
├── GOOGLE_DRIVE_SETUP.md     # Google Drive 設定說明
└── README.md                  # 本文件
```

## 故障排除

### LINE Bot 沒反應
1. 檢查 FastAPI 服務器是否運行（終端應顯示日誌）
2. 檢查 ngrok 是否運行
3. 確認 LINE Webhook URL 是最新的 ngrok 網址
4. 查看 FastAPI 終端的日誌輸出

### PDF 無圖片
- 檢查 `product_images_2` 表是否有對應的 `product_id`
- 檢查圖片路徑是否正確
- 查看終端日誌中的圖片下載狀態

### Google Drive 上傳失敗
- 確認 `google-credentials.json` 存在且正確
- 確認服務帳號有權限訪問指定的資料夾
- 檢查 `.env` 中的 `GOOGLE_DRIVE_FOLDER_ID` 是否正確
