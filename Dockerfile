FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper/ ./scraper/
COPY assistant/ ./assistant/
COPY deploy/ ./deploy/
COPY main.py .

RUN mkdir -p /app/articles /app/chroma_db

CMD ["python", "main.py"]
