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

# Setup startup script with screen
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'Xvfb :0 -screen 0 1024x768x24 &' >> /app/start.sh && \
    echo 'screen -dmS scraper python -u instagram_scraper.py' >> /app/start.sh && \
    echo 'screen -r scraper' >> /app/start.sh && \
    chmod +x /app/start.sh

# Default command (can be overridden by docker-compose)
CMD ["/bin/bash", "/app/start.sh"] 