FROM python:3.11-slim

RUN pip install --no-cache-dir flask==3.* && \
    apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py ./
COPY data/ ./data/
COPY secret_admin.txt ./
COPY repro/ ./repro/
RUN chmod +x repro/*.sh

CMD ["sh"]
