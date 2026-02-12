# Agent RAG - Sales Analyst with Document Search

An AI-powered sales analyst agent that combines document search with SQL database queries. Uses Google ADK to provide intelligent analysis of sales data and forecast documents.

## Features

- **Agent-Based Architecture**: Uses Google ADK for intelligent task orchestration
- **Document Search**: RAG-based search through forecast and planning documents
- **SQL Database Queries**: Direct queries against sales transaction data
- **Metrics Calculation**: Variance analysis, YoY comparisons, growth rates
- **Multiple Format Support**: PDF, TXT, and other document formats (via PyMuPDF or Docling)
- **Vector Search**: Uses ChromaDB for efficient document retrieval

## Prerequisites

Before installing, make sure you have:

1. **Python 3.8+** installed
2. **Ollama** installed and running ([Download here](https://ollama.ai))
3. Required Ollama models:
   ```bash
   ollama pull granite-embedding:30m
   ollama pull gemma3:4b
   ```

## Installation

1. Clone or download this repository

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (fast Python package manager):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Create virtual environment and install dependencies:

   ```bash
   uv sync
   ```

4. Set up environment variables:

   Create a `.env` file in the `my_agent/` directory with:
   ```bash
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Usage

### Running the Agent (Recommended)

Start the agent web interface:

```bash
adk web --port 8000
```

Then open your browser to `http://localhost:8000` to interact with the sales analyst agent.

### Example Queries

- "Show me sales for 2025"
- "What was Q4 performance by category?"
- "Compare actual sales to the forecast"
- "Calculate year-over-year growth for Electronics"

### Standalone Scripts

You can also use the scripts directly:

**Initialize the database:**

```bash
uv run python db/init_db.py
```

**Index a document:**

```bash
uv run python index.py /path/to/document.pdf
```

**Ask a question:**

```bash
uv run python query.py "What is the main topic of the document?"
```

## Agent Tools

The sales analyst agent has access to three specialized tools:

### `search_documents`
RAG-based search through indexed forecast and planning documents. Use this to find information about projections, plans, and forecasts.

### `query_sales`
Execute SQL queries against the sales database. The database contains transaction data with columns: id, date, year, month, category, amount.

### `calculate_metrics`
Perform variance analysis, year-over-year comparisons, and growth rate calculations on sales data.

## Configuration

You can modify these settings in `index.py` and `query.py`:

- `OLLAMA_API_BASE`: Ollama API endpoint (default: `http://localhost:11434`)
- `EMBEDDING_MODEL`: Model for embeddings (default: `granite-embedding:30m`)
- `GENERATION_MODEL`: Model for chat/generation (default: `nemotron-3-nano-30b-a3b:free`)
- `CHROMA_DB_PATH`: Database storage location (default: `./chromadb_storage`)

## Project Structure

```
NaiveRag/
├── main.py              # Main interactive interface
├── index.py             # Document indexing pipeline
├── query.py             # Question-answering pipeline
├── db/
│   ├── init_db.py       # Database initialization script
│   └── sales.db         # SQLite sales database
├── my_agent/
│   ├── __init__.py
│   ├── agent.py         # ADK agent definition
│   └── tools/
│       ├── __init__.py
│       ├── search_documents.py
│       ├── query_sales.py
│       └── calculate_metrics.py
├── documents/           # Forecast documents to index
├── requirements.txt     # Python dependencies
└── chromadb_storage/    # Vector database (created automatically)
```

## Troubleshooting

**"Model not found" error:**

- Make sure Ollama is running: `ollama serve`
- Pull the required models (see Prerequisites)

**"No relevant information found":**

- Index some documents first using `uv run python index.py`
- Try rephrasing your question

**Import errors:**

- Make sure your virtual environment is activated
- Install dependencies: `uv sync`

**Agent not starting:**

- Verify `OPENROUTER_API_KEY` is set in `my_agent/.env`
- Check that Google ADK is installed: `uv pip install google-adk`

## Privacy & Security

- Document processing happens locally using Ollama
- Documents are stored in the local ChromaDB database
- Sales data is stored in local SQLite database
- API keys are required only for the agent LLM backend

## License

This project is provided as-is for educational and personal use.
