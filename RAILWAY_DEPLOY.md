# 🚂 Railway 部署完整指南

## 📋 前置準備

### 1. 註冊 Railway 帳號
前往 [Railway.app](https://railway.app/) 並使用 GitHub 帳號登入

### 2. 註冊 GitHub 帳號（如果還沒有）
前往 [GitHub.com](https://github.com/) 註冊

---

## 🚀 部署步驟

### 步驟 1：將程式碼上傳到 GitHub

#### 1.1 初始化 Git（在專案目錄執行）

```bash
cd /Users/hsiehjiapei/Desktop/line_pdf
git init
git add .
git commit -m "Initial commit: LINE PDF Generator"
```

#### 1.2 在 GitHub 建立新 Repository

1. 前往 https://github.com/new
2. Repository name: `line-pdf-generator`
3. 設定為 **Private** （保護您的程式碼）
4. 不要勾選任何初始化選項
5. 點擊 "Create repository"

#### 1.3 推送程式碼到 GitHub

```bash
git remote add origin https://github.com/你的使用者名稱/line-pdf-generator.git
git branch -M main
git push -u origin main
```

---

### 步驟 2：在 Railway 建立專案

1. 登入 [Railway Dashboard](https://railway.app/dashboard)
2. 點擊 **"New Project"**
3. 選擇 **"Deploy from GitHub repo"**
4. 如果是第一次，需要授權 Railway 存取 GitHub
5. 選擇 `line-pdf-generator` repository
6. Railway 會自動開始部署

---

### 步驟 3：設定環境變數

在 Railway 專案頁面：

1. 點擊您的服務
2. 選擇 **"Variables"** 分頁
3. 點擊 **"Add Variable"** 並逐一新增：

```
SUPABASE_URL=你的_supabase_url
SUPABASE_SERVICE_ROLE_KEY=你的_supabase_key
LINE_CHANNEL_SECRET=你的_line_secret
LINE_CHANNEL_ACCESS_TOKEN=你的_line_token
```

**重要：不要上傳 `google-credentials.json` 到 GitHub！**
（Google Drive 功能暫時無法使用，但 Supabase 儲存仍可正常運作）

4. 點擊 **"Deploy"** 重新部署

---

### 步驟 4：取得 Railway URL

1. 在專案頁面，點擊 **"Settings"**
2. 找到 **"Domains"** 區域
3. 點擊 **"Generate Domain"**
4. 會得到類似：`your-app.up.railway.app` 的網址
5. **複製這個網址**

---

### 步驟 5：更新 LINE Webhook URL

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇您的 Channel
3. 進入 **"Messaging API"** 分頁
4. 找到 **"Webhook URL"**
5. 填入：
   ```
   https://your-app.up.railway.app/line/webhook
   ```
6. 點擊 **"Update"**
7. 點擊 **"Verify"** 測試連線（應該顯示成功）

---

## ✅ 測試

1. 在 LINE 聊天室傳送「下載購物單」
2. 應該會收到 PDF 下載連結
3. 完成！🎉

---

## 📊 監控和 Logs

### 查看 Logs
在 Railway 專案頁面：
1. 點擊您的服務
2. 選擇 **"Deployments"** 分頁
3. 點擊最新的部署
4. 可以看到即時 logs

### 查看使用量
在專案頁面可以看到：
- CPU 使用率
- 記憶體使用
- 網路流量
- 每月費用

---

## 💰 費用說明

Railway 免費方案：
- **每月 $5 免費額度**
- 約可運行 500 小時（約 20 天 24/7 運行）
- 超過需要付費（$0.000231/分鐘）

**建議：**
- 如果流量不大，免費額度通常足夠
- 可以設定用量警報

---

## 🔧 常見問題

### Q: 如何更新程式碼？

```bash
cd /Users/hsiehjiapei/Desktop/line_pdf
git add .
git commit -m "更新說明"
git push
```

Railway 會自動偵測並重新部署！

### Q: 部署失敗怎麼辦？

1. 檢查 Railway Logs
2. 確認所有環境變數都設定正確
3. 確認 `requirements.txt` 包含所有套件

### Q: Playwright 錯誤？

Railway 的 Nixpacks 會自動安裝 Playwright 相依套件，如果還是有問題，在 Railway Variables 加入：

```
PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright
```

### Q: 想要自訂網址？

Railway 專案 > Settings > Domains > "Custom Domain"
（需要擁有網域名稱）

---

## 📞 需要協助？

- Railway 文檔: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway

---

## 🎯 下一步優化建議

1. **設定 Custom Domain**（更專業的網址）
2. **加入錯誤通知**（部署失敗時收到通知）
3. **設定 Health Check**（確保服務持續運行）
4. **增加資料庫備份**（定期備份 Supabase）

恭喜您完成部署！🎉
