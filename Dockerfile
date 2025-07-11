FROM python:3.9-slim

WORKDIR /app

# 0) Install OS-level build deps so psycopg2 can compile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1) Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Copy your code in
COPY . .
