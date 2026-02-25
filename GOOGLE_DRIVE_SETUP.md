# Google Drive 設定說明

## 步驟 1: 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 點擊右上角的專案選擇器
3. 點擊 "新增專案"
4. 輸入專案名稱，例如：`LINE PDF Generator`
5. 點擊 "建立"

## 步驟 2: 啟用 Google Drive API

1. 在 Google Cloud Console 左側選單，選擇 "API 和服務" > "啟用的 API 和服務"
2. 點擊 "+ 啟用 API 和服務"
3. 搜尋 "Google Drive API"
4. 點擊進入，然後點擊 "啟用"

## 步驟 3: 建立服務帳號

1. 在左側選單選擇 "API 和服務" > "憑證"
2. 點擊 "+ 建立憑證" > "服務帳號"
3. 輸入服務帳號名稱，例如：`line-pdf-uploader`
4. 點擊 "建立並繼續"
5. 角色選擇：**無需設定**（或選擇 "基本" > "檢視者"）
6. 點擊 "繼續" > "完成"

## 步驟 4: 下載 JSON 金鑰

1. 在憑證頁面，找到剛才建立的服務帳號
2. 點擊服務帳號的電子郵件地址
3. 切換到 "金鑰" 分頁
4. 點擊 "新增金鑰" > "建立新金鑰"
5. 選擇 "JSON" 格式
6. 點擊 "建立"
7. JSON 檔案會自動下載

## 步驟 5: 放置金鑰檔案

1. 將下載的 JSON 檔案重新命名為 `google-credentials.json`
2. 將檔案移動到專案根目錄：
   ```
   /Users/hsiehjiapei/Desktop/line_pdf/google-credentials.json
   ```

## 步驟 6: （可選）建立專用資料夾

如果您想將所有 PDF 上傳到特定的 Google Drive 資料夾：

1. 在 Google Drive 建立一個新資料夾，例如：`LINE購物單`
2. 在資料夾網址中複製資料夾 ID：
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                        ^^^^^^^^^^^^^^^^^^^^^^^^
                                        這就是資料夾 ID
   ```
3. 在 `.env` 檔案中加入：
   ```
   GOOGLE_DRIVE_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j
   ```

## 測試

設定完成後，重新啟動服務並在 LINE 測試「下載購物單」功能。

PDF 將會：
- 上傳到 Google Drive
- 自動設定為任何人都可查看
- 返回分享連結給 LINE

## 疑難排解

### 錯誤：找不到 google-credentials.json
確認檔案路徑正確：`/Users/hsiehjiapei/Desktop/line_pdf/google-credentials.json`

### 錯誤：權限不足
確認已啟用 Google Drive API

### 圖片還是無法顯示
這是正常的，因為圖片在 PDF 生成時就會嵌入，不會再從外部載入。
