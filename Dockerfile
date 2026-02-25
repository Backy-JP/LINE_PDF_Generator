# 使用 Python 3.9 作為基礎映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（Playwright Chromium 需要）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 瀏覽器
RUN playwright install chromium
RUN playwright install-deps chromium

# 複製應用程式代碼
COPY . .

# 暴露端口（Railway 會自動設定 PORT 環境變數）
EXPOSE 8080

# 啟動命令
CMD ["sh", "-c", "echo 'Starting application...' && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
