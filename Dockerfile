FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libx11-xcb1 \
    xdg-utils \
    fonts-liberation \
    screen \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome using the updated method
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list > /dev/null \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/data /app/sessions && chmod 777 /app/data /app/sessions

# Set environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf8
# Required for undetected-chromedriver
ENV DISPLAY=:0
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null

# Create helper scripts
RUN echo '#!/bin/bash' > /app/start-scraper.sh && \
    echo 'screen -S scraper python -u instagram_scraper.py' >> /app/start-scraper.sh && \
    chmod +x /app/start-scraper.sh

RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'Xvfb :0 -screen 0 1024x768x24 &' >> /app/start.sh && \
    echo 'echo "Instagram Scraper Container"' >> /app/start.sh && \
    echo 'echo "------------------------"' >> /app/start.sh && \
    echo 'echo "Commands available:"' >> /app/start.sh && \
    echo 'echo "1. ./start-scraper.sh    - Start a new scraper session"' >> /app/start.sh && \
    echo 'echo "2. screen -r scraper     - Reconnect to existing session"' >> /app/start.sh && \
    echo 'echo "3. screen -ls            - List running sessions"' >> /app/start.sh && \
    echo 'echo ""' >> /app/start.sh && \
    echo 'echo "To detach from a running session: Press Ctrl+A, then D"' >> /app/start.sh && \
    echo 'echo "------------------------"' >> /app/start.sh && \
    echo 'exec bash' >> /app/start.sh && \
    chmod +x /app/start.sh

# Default command (can be overridden by docker-compose)
CMD ["/bin/bash", "/app/start.sh"] 