FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Chrome for Selenium
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/config /app/logs

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY smartschool_monitor_v2.py .
COPY selenium_login.py .

# Environment variables (can be overridden in docker-compose)
ENV SCHEDULES="12:00,16:00,20:00"
ENV NOTIFIERS=""
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "smartschool_monitor_v2.py"]
