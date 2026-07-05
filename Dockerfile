FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper/ ./scraper/
COPY main.py .

RUN mkdir -p /app/articles
VOLUME ["/app/articles"]

CMD ["python", "main.py"]
