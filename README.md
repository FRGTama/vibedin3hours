# OptiBot Mini-Clone

A customer-support chatbot for OptiSigns.com that scrapes support articles, builds a vector knowledge base, and answers questions with citations.

## Architecture

```
scraper/          # Zendesk API → Markdown articles
assistant/        # RAG pipeline: chunk → embed → ChromaDB → Gemini
deploy/           # S3 state sync for Railway deployment
main.py           # Daily job: scrape + ingest
```

## Setup

```bash
cp .env.sample .env
# Fill in: ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN, GEMINI_API_KEY
pip install -r requirements.txt
```

## Run Locally

### Ingest articles (run once or daily)
```bash
python -m assistant.cli ingest
```

### Ask a question
```bash
python -m assistant.cli ask "How do I add a YouTube video?"
```

### Run full pipeline (scrape + ingest)
```bash
python main.py
```

## Docker

```bash
docker build -t optibot .
docker run --env-file .env optibot
```

## Railway Deployment

### 1. Create S3 bucket for state persistence
```bash
aws s3 mb s3://optibot-state
aws iam create-user --user-name optibot
aws iam put-user-policy --user-name optibot --policy-name S3Access \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:*"],"Resource":"arn:aws:s3:::optibot-state/*"}]}'
aws iam create-access-key --user-name optibot
```

### 2. Deploy to Railway
1. Push repo to GitHub
2. In Railway: **New Project → Deploy from GitHub repo**
3. Add environment variables:
   - `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN`
   - `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash-lite`, `EMBEDDING_MODEL=gemini-embedding-001`
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION=us-east-1`
   - `S3_BUCKET=optibot-state`, `S3_PREFIX=state/`
4. **Settings → Cron**: `0 0 * * *` (midnight UTC daily)

### 3. View logs
Railway dashboard → your service → **Deployments → Logs**

## Chunking Strategy

Recursive chunking: headings (H1/H2/H3) → paragraphs → sentences.
- Max chunk size: 800 tokens (~3200 chars)
- Overlap: 150 tokens (~600 chars)
- Metadata per chunk: `article_id`, `slug`, `url`, `heading_path`

Delta detection: SHA256 hash per chunk, only changed chunks are re-embedded.

## OptiBot System Prompt

```
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
```

## Sample Question

> "How do I add a YouTube video?"

*(Screenshot placeholder — run `python -m assistant.cli ask "How do I add a YouTube video?"` after ingest)*
