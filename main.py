import os
import hmac
import base64
import hashlib
import io
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright
from jinja2 import Template
import httpx
from datetime import datetime
from PIL import Image
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

load_dotenv()

app = FastAPI()

# ========= 環境變數 =========
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========= 驗證 LINE 簽章 =========
def verify_signature(body, signature):
    hash = hmac.new(
        LINE_SECRET.encode(),
        body,
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash).decode() == signature

# ========= 產 PDF =========
async def generate_pdf(html):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        
        # 設定較長的超時時間
        page.set_default_timeout(30000)
        
        await page.set_content(html, wait_until="load")
        
        # Base64 圖片不需要等待網路加載，稍微等待一下讓圖片渲染
        try:
            await page.wait_for_timeout(1000)
        except:
            pass
        
        # 生成 PDF
        pdf = await page.pdf(
            format="A4",
            print_background=True,
            prefer_css_page_size=True
        )
        await browser.close()
        return pdf

# ========= 上傳到 Google Drive =========
def upload_to_google_drive(pdf_bytes, filename):
    """上傳 PDF 到 Google Drive 並返回可分享的連結"""
    try:
        # 載入服務帳號憑證
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        # 建立 Drive API 服務
        service = build('drive', 'v3', credentials=credentials)
        
        # 準備檔案元數據
        file_metadata = {
            'name': filename,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]  # 指定上傳到哪個資料夾
        }
        
        # 將 bytes 轉換為 BytesIO 物件
        file_stream = io.BytesIO(pdf_bytes)
        media = MediaIoBaseUpload(file_stream, mimetype='application/pdf', resumable=True)
        
        # 上傳檔案
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        print(f"✅ 檔案已上傳到 Google Drive，檔案ID: {file_id}")
        
        # 設定檔案權限為任何人都可以查看
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        # 生成可分享的連結
        download_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        print(f"✅ 分享連結: {download_link}")
        
        return download_link
        
    except Exception as e:
        print(f"❌ Google Drive 上傳失敗: {e}")
        return None

# ========= Webhook =========
@app.post("/line/webhook")
async def webhook(request: Request):
    try:
        body = await request.body()
        signature = request.headers.get("X-Line-Signature")

        if not verify_signature(body, signature):
            print("❌ 簽章驗證失敗")
            return {"error": "Invalid signature"}

        data = await request.json()
        event = data["events"][0]
        print("=== LINE EVENT ===")
        print(event)

        reply_token = event.get("replyToken")
        print(f"Reply Token: {reply_token}")

        trigger = False

        # 1) Postback
        if event.get("type") == "postback":
            trigger = True
            print("✅ Postback 事件觸發")

        # 2) Rich Menu 文字
        if event.get("type") == "message":
            msg = event.get("message", {})
            print(f"收到訊息類型: {msg.get('type')}, 內容: {msg.get('text')}")
            if msg.get("type") == "text" and msg.get("text") == "下載購物單":
                trigger = True
                print("✅ 文字訊息觸發")

        if not trigger:
            print("ℹ️ 未觸發，忽略此事件")
            return {"status": "ignored"}
        
        print("🚀 開始處理購物單生成...")

        # ---- 1️⃣ 查資料 ----
        items = supabase.table("order_items").select(
            "order_id,product_id,qty,created_at"
        ).order("created_at", desc=True).limit(10).execute()  # 限制 10 筆以控制檔案大小
        print(f"查詢到 {len(items.data)} 筆商品（最新 10 筆）")

        # 查詢圖片
        images = supabase.table("product_images_2").select(
            "product_id,image_path"
        ).execute()
        print(f"查詢到 {len(images.data)} 筆圖片")

        # 建立 product_id -> 圖片 Base64 的對應表
        image_map = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for img in images.data:
                pid = img.get("product_id")
                path = img.get("image_path")
                
                if not pid or not path:
                    continue

                # 同商品多圖：只取第一張
                if pid in image_map:
                    continue

                try:
                    # 取得圖片 URL
                    if str(path).startswith("http"):
                        img_url = path
                    else:
                        signed = supabase.storage.from_("Product_images").create_signed_url(str(path), 600)
                        img_url = signed.get("signedURL") or signed.get("signed_url")
                    
                    if not img_url:
                        continue
                    
                    # 下載圖片
                    print(f"📥 下載圖片: 產品 {pid}")
                    response = await client.get(img_url)
                    if response.status_code == 200:
                        # 壓縮圖片並轉成 Base64
                        img_data = response.content
                        img = Image.open(BytesIO(img_data))
                        
                        # 轉換為 RGB（如果是 RGBA）
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # 調整大小並壓縮
                        img.thumbnail((80, 80), Image.Resampling.LANCZOS)
                        
                        # 轉成 Base64
                        buffered = BytesIO()
                        img.save(buffered, format="JPEG", quality=60, optimize=True)
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        
                        image_map[pid] = f"data:image/jpeg;base64,{img_base64}"
                        print(f"✅ 產品 {pid} 圖片處理完成 ({len(img_base64)} bytes)")
                    else:
                        print(f"⚠️ 產品 {pid} 圖片下載失敗: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ 產品 {pid} 圖片處理失敗: {str(e)}")
                    continue

        print(f"✅ 成功處理 {len(image_map)} 個產品的圖片")

        # 建立結果列表
        result = []
        for item in items.data:
            result.append({
                "order_id": item["order_id"],
                "product_id": item["product_id"],
                "qty": item["qty"],
                "created_at": item["created_at"],
                "image_data": image_map.get(item["product_id"])
            })

        # ---- 2️⃣ HTML 模板 ----
        html_template = """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: 'Microsoft JhengHei', Arial, sans-serif; 
                    margin: 20px;
                    color: #333;
                }
                h2 {
                    color: #2c3e50;
                    border-bottom: 3px solid #A8D8EA;
                    padding-bottom: 10px;
                }
                .info {
                    color: #666;
                    margin: 10px 0;
                    font-size: 14px;
                }
                table { 
                    border-collapse: collapse; 
                    width: 100%;
                    margin-top: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                th { 
                    background-color: #A8D8EA;  /* 寶寶藍 */
                    color: #000000;  /* 黑色文字 */
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: bold;
                    border: 1px solid #87CEEB;
                }
                td {
                    padding: 10px 8px;
                    border: 1px solid #ddd;
                    vertical-align: middle;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                tr:hover {
                    background-color: #f0f8ff;
                }
                /* 圖片欄位 */
                .col-image {
                    width: 80px;
                    text-align: center;
                }
                /* 訂單編號欄位 - 調小 */
                .col-order {
                    width: 200px;
                    text-align: center;
                    font-size: 16px;
                }
                /* 商品編號欄位 */
                .col-product {
                    width: auto;
                    text-align: center;
                }
                /* 數量欄位 - 加寬避免換行 */
                .col-qty {
                    width: 70px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 16px;
                    color: #000000;
                }
                img {
                    display: block;
                    margin: 0 auto;
                    max-width: 60px;
                    max-height: 60px;
                    object-fit: cover;
                    border-radius: 4px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                }
                .no-image {
                    color: #999;
                    font-style: italic;
                    font-size: 11px;
                }
            </style>
        </head>
        <body>
        <h2>📋 購物單報表</h2>
        <div class="info">
            <p><strong>⏰ 匯出時間：</strong>{{time}}</p>
            <p><strong>📊 總計：</strong>{{total}} 筆商品</p>
        </div>
        <table>
        <thead>
        <tr>
            <th class="col-image">圖片</th>
            <th class="col-order">訂單編號</th>
            <th class="col-product">商品編號</th>
            <th class="col-qty">數量</th>
        </tr>
        </thead>
        <tbody>
        {% for item in items %}
        <tr>
            <td class="col-image">
                {% if item.image_data %}
                <img src="{{item.image_data}}" alt="Product {{item.product_id}}">
                {% else %}
                <span class="no-image">無圖片</span>
                {% endif %}
            </td>
            <td class="col-order">{{item.order_id}}</td>
            <td class="col-product">{{item.product_id}}</td>
            <td class="col-qty">{{item.qty}}</td>
        </tr>
        {% endfor %}
        </tbody>
        </table>
        </body>
        </html>
        """

        template = Template(html_template)
        html = template.render(
            items=result,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=len(result)
        )
        print(f"✅ HTML 模板渲染完成，共 {len(result)} 筆資料")

        # ---- 3️⃣ 產 PDF ----
        print("📄 開始生成 PDF...")
        pdf_bytes = await generate_pdf(html)
        print(f"✅ PDF 生成完成，大小: {len(pdf_bytes)} bytes ({len(pdf_bytes)/1024:.2f} KB)")
        
        # 檢查檔案大小
        max_size = 10 * 1024 * 1024  # 10MB
        if len(pdf_bytes) > max_size:
            error_msg = f"PDF 檔案太大 ({len(pdf_bytes)/1024/1024:.2f}MB)"
            print(f"❌ {error_msg}")
            
            # 回傳錯誤訊息給 LINE
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://api.line.me/v2/bot/message/reply",
                    headers={"Authorization": f"Bearer {LINE_TOKEN}"},
                    json={
                        "replyToken": reply_token,
                        "messages": [{"type": "text", "text": f"❌ {error_msg}"}]
                    }
                )
            return {"error": error_msg}
        
        # 準備檔案名稱
        file_name = f"shopping_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        print(f"📤 上傳 PDF 到 Google Drive: {file_name}")

        try:
            # 上傳到 Google Drive
            download_url = upload_to_google_drive(pdf_bytes, file_name)
            
            if not download_url:
                print(f"❌ Google Drive 上傳失敗")
                # 回傳錯誤訊息給 LINE
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://api.line.me/v2/bot/message/reply",
                        headers={"Authorization": f"Bearer {LINE_TOKEN}"},
                        json={
                            "replyToken": reply_token,
                            "messages": [{"type": "text", "text": f"❌ 上傳失敗，請稍後再試"}]
                        }
                    )
                return {"error": "Google Drive upload failed"}
            
            print(f"✅ Google Drive 連結: {download_url}")
            
        except Exception as upload_error:
            error_msg = f"上傳失敗: {str(upload_error)}"
            print(f"❌ {error_msg}")
            
            # 回傳錯誤訊息給 LINE
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://api.line.me/v2/bot/message/reply",
                    headers={"Authorization": f"Bearer {LINE_TOKEN}"},
                    json={
                        "replyToken": reply_token,
                        "messages": [{"type": "text", "text": f"❌ 上傳失敗，請稍後再試"}]
                    }
                )
            return {"error": error_msg}

        # ---- 4️⃣ 回 LINE ----
        print(f"💬 準備回覆 LINE (reply_token: {reply_token})...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={
                    "Authorization": f"Bearer {LINE_TOKEN}"
                },
                json={
                    "replyToken": reply_token,
                    "messages": [
                        {
                            "type": "text",
                            "text": f"✅ 購物單已生成！\n\n📄 Google Drive 連結：\n{download_url}\n\n📊 共 {len(result)} 筆資料"
                        }
                    ]
                }
            )
            print(f"LINE API 回應狀態: {response.status_code}")
            print(f"LINE API 回應內容: {response.text}")

        print("✅ 處理完成")
        return {"status": "ok"}
    
    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}