# Assistant

RAG-powered OptiBot customer-support assistant using Google Gemini (embeddings + LLM) and ChromaDB.

## Setup

### 1. Create a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in and click "Get API Key"
3. Copy the key

### 2. Configure Environment

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=gemini-embedding-001
CHROMA_DB_PATH=chroma_db
CHROMA_COLLECTION=optisigns_docs
ARTICLES_DIR=articles
CHUNK_MAX_TOKENS=800
CHUNK_OVERLAP_TOKENS=150
TOP_K=5
```

### 3. Install Dependencies

```bash
pip install google-genai chromadb
```

## Usage

### Ingest Articles & Query

```bash
python assistant/cli.py "How do I add a YouTube video?"
```

This will:
1. Read all `.md` files from `articles/`
2. Chunk them recursively (headings → paragraphs → sentences)
3. Generate embeddings via `gemini-embedding-001`
4. Upsert into ChromaDB
5. Query using `gemini-2.0-flash` + OptiBot system prompt
6. Output JSON with answer and citations

### JSON Output Example

```json
{
  "answer": "To add a YouTube video:\n1. Open your OptiSigns dashboard...",
  "citations": [
    {"url": "https://support.optisigns.com/hc/en-us/articles/123456", "title": "How to Add a YouTube Video"},
    {"url": "https://support.optisigns.com/hc/en-us/articles/789012", "title": "Managing Your Playlist"}
  ]
}
```

## Chunking Strategy

**Recursive chunking** splits content in this order:

| Step | Split by | Max size | Overlap |
|------|----------|----------|---------|
| 1 | Headings (H1/H2/H3) | — | — |
| 2 | Paragraphs (`\n\n`) | 800 tokens | 150 tokens |
| 3 | Sentences (`.!?`) | 800 tokens | 150 tokens |

Each chunk carries metadata: `article_id`, `slug`, `url`, `heading_path`.

Delta detection compares SHA256 of each chunk against previously stored hashes in ChromaDB. Only changed chunks are re-embedded and upserted.

## Create Assistant in Google AI Studio

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Create a new structured prompt
3. Set the **System Instruction** to:

```
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
```

4. Test with: "How do I add a YouTube video?"
5. Take a screenshot showing the answer with citations

## Architecture

```
assistant/
├── interfaces.py   # Chunk, RetrievalResult, Answer dataclasses + ABCs
├── config.py       # Gemini API key, models, ChromaDB, chunk settings
├── chunker.py      # RecursiveChunker (headings→paragraphs→sentences)
├── embedder.py     # GeminiEmbedder (gemini-embedding-001, batch support)
├── vector_store.py # ChromaVectorStore (persist, upsert, query, delta tracking)
├── generator.py    # GeminiGenerator (LLM + OptiBot prompt, JSON output)
├── assistant.py    # AssistantOrchestrator (ingest + query coordination)
├── cli.py          # CLI entry point
└── README.md
```
