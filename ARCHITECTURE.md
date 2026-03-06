# 🏛️ Mutual Fund RAG Chatbot: Architecture & Design

This document outlines the end-to-end architecture for a production-ready RAG (Retrieval Augmented Generation) chatbot that provides grounded, data-backed information about mutual funds sourced exclusively from INDmoney.

---

## 🎯 Project Overview
- **Domain**: Mutual funds (sourced from `https://www.indmoney.com/mutual-funds`).
- **Core Technology Stack**:
  - **Backend**: Python (FastAPI), Groq API (`llama3-70b-8192`), Playwright, ChromaDB, Sentence-Transformers.
  - **Frontend**: React (with smooth aesthetics and mobile responsiveness).
  - **CI/CD & Cron**: GitHub Actions.
  - **Containerization**: Docker & Docker Compose.

---

## 🧩 Architectural Constraints & Domain Rules
1. **Strict Context Grounding**: LLM answers must be strictly grounded in the retrieved context. No hallucinations or general investment knowledge.
2. **Answer Length**: Answers are constrained to ≤3 sentences.
3. **Traceability**: Every answer must append the source URL from which the data was retrieved.
4. **Scope Guarding**: The system must reject investment advice, opinions, PII, and unrelated topics with a polite, consistent refusal.
5. **AI Suggestions**: On every load, surface 3 AI-suggested questions derived from the available context.

---

## 🚀 Getting Started (Local Setup)

This project is optimized for local execution and seamless deployment to **Vercel**.

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Groq API Key** (Sourced from [Groq Console](https://console.groq.com/))

### 2. Backend & Scraper Configuration
1. **Create a Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
3. **Install Browser Binaries**:
   ```powershell
   playwright install chromium
   ```
4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and add your `GROQ_API_KEY`.

### 3. Frontend Configuration
1. Navigate to the frontend directory:
   ```powershell
   cd Phase4_Frontend/frontend
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Start the dev server:
   ```powershell
   npm run dev
   ```

---

## 🌐 Deployment (Vercel)

This project is designed to be deployed as a **Vercel Monorepo**:

1. **Frontend**: The React application will be deployed as the main frontend.
2. **Backend**: The FastAPI app will be served via **Vercel Serverless Functions** (using the `api/` directory mapping).
3. **Scraper & Database**:
   - **ChromaDB**: Since Vercel is serverless, persistent local storage (`data/chroma`) is not suitable for high-traffic production. For Vercel deployment, ChromaDB should be used in **Client/Server mode** pointing to a managed instance (e.g., Chroma Cloud) or replaced with a serverless-friendly vector store (e.g., Pinecone/Supabase Vector).
   - **Scraper**: The Playwright scraper will run via **GitHub Actions** (Phase 5) and push updates to the remote vector database.

---

```ascii
[ User (React UI) ] 
       │
       │ (1. POST /chat or GET /suggestions)
       ▼
[ FastAPI Backend ] ◄─────────┐
       │                      │
       │ (2. Embedding &      │ (6. Formatted Response + 
       │     Semantic Search) │     Source URL + Suggestions)
       ▼                      │
[ ChromaDB (Vector) ] ◄──┐    │
[ JSON Snapshots (Raw) ] ──┘    │
       │                      │
       │ (3. Top-k Chunks)    │
       ▼                      │
[ LLM Gateway (Groq) ] ───────┘
       │
       │ (4. Prompt template + Context chunks)
       ▼
[ llama3-70b-8192 ] ─── (5. Refined Answer) ───▶
```

---

## 📅 Phases Breakdown

### Phase 1 — Scraping & Storage
#### Module: `scraper/`
- **Tool**: Playwright (Headless/Auto-scrolling).
- **Target**: INDmoney Mutual Fund pages.
- **Data Points**:
  1. **Fund Name & House**: Name of the scheme and the AMC.
  2. **Fund Category**: Equity, Debt, Hybrid, etc.
  3. **Fund Manager**: Names of the individuals managing the fund.
  4. **NAV**: Current Net Asset Value.
  5. **1Y / 3Y / 5Y Returns (%)**: Historical performance metrics.
  6. **Benchmark Comparison**: How the fund compares against its benchmark.
  7. **Alpha**: Excess returns relative to the benchmark.
  8. **Risk Rating**: Risk level (e.g., Very High).
  9. **Standard Deviation**: Volatility measure.
  10. **Sharpe Ratio**: Risk-adjusted return measure.
  11. **Expense Ratio (%)**: Annual fee charged by the fund.
  12. **AUM**: Assets Under Management.
  13. **Exit Load**: Charges on early redemption.
  14. **Minimum Investment**: Lumpsum and SIP amounts.
  15. **Lock-in Period**: If applicable (e.g., ELSS).
- **Target URLs**:
  - `https://www.indmoney.com/mutual-funds/dsp-world-gold-mining-overseas-equity-omni-fof-direct-plan-growth-5457`
  - `https://www.indmoney.com/mutual-funds/lic-mf-gold-etf-fof-direct-growth-3721`
  - `https://www.indmoney.com/mutual-funds/icici-prudential-bharat-22-fof-direct-growth-5380`
  - `https://www.indmoney.com/mutual-funds/quant-small-cap-fund-growth-option-direct-plan-611`
  - `https://www.indmoney.com/mutual-funds/hdfc-infrastructure-fund-direct-plan-growth-option-3315`
  - `https://www.indmoney.com/mutual-funds/icici-prudential-credit-risk-fund-direct-plan-growth-378`
  - `https://www.indmoney.com/mutual-funds/kotak-multi-asset-omni-fof-direct-growth-3723`
  - `https://www.indmoney.com/mutual-funds/nippon-india-multi-asset-allocation-fund-direct-growth-1005954`
  - `https://www.indmoney.com/mutual-funds/edelweiss-aggressive-hybrid-direct-plan-growth-option-4633`
  - `https://www.indmoney.com/mutual-funds/mahindra-manulife-aggressive-hybrid-fund-direct-growth-1004900`

#### Tradeoffs & Design Decisions:
- **Playwright over BeautifulSoup**: INDmoney is a modern SPA with JavaScript-rendered content. Playwright ensures we capture the actual visible state.
- **URL Hash Deduping**: Most efficient way to avoid process-heavy diffing; if the URL is the same, we check the NAV or last-scraped date before updating.

---

### Phase 2 — Embedding & Retrieval
#### Module: `ingestion/` & `search/`
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence-Transformers).
- **Vector Store**: ChromaDB (lightweight, persist-to-disk).
- **Retrieval Strategy**:
  - Semantic Search: Top-k (k=3 or 4) retrieved chunks.
  - Metadata Filtering: Ensure `source_url` and `scraped_at` are passed to the retrieval results.

#### Tradeoffs & Design Decisions:
- **`all-MiniLM-L6-v2`**: Chosen for low latency and small memory footprint while maintaining high semantic accuracy.
- **Local Persistence**: ChromaDB is used without a dedicated server process to simplify deployment in initial phases.

---

### Phase 3 — Backend API
#### Module: `api/`
- **Framework**: FastAPI.
- **Endpoints**:
  - `POST /chat`: Receives user message, runs scope guard, retrieves context, queries Groq, returns answer + source + suggestions.
  - `GET /suggestions`: Returns 3 global trending questions based on indexed fund categories.
  - `GET /health`: Basic health check for Uptime monitoring.
- **Middleware / Filters**:
  - **Scope Guard**: A lightweight classifier (LLM-based or keyword-based) that stops queries like "Which stock should I buy?" or "What is my bank account number?".

#### Tradeoffs & Design Decisions:
- **LLM for Scope Guarding**: Using a small Groq model or specific prompt instruction to classify "is_in_scope: boolean" before full retrieval saves tokens and prevents leakage.

---

### Phase 4 — Frontend
#### Module: `frontend/`
- **Framework**: React (Vite).
- **UI Components**:
  - **Chat Thread**: Bubble-style messages.
  - **Suggestion Chips**: Clickable buttons at the bottom of the input.
  - **Source Link Rendering**: Distinctive UI element showing "Source: [link_text](url)".
  - **Refusal Handler**: Elegant styled refusal messages for out-of-scope queries (e.g., "I'm sorry, I can only assist with mutual fund-specific details from INDmoney.").

#### Tradeoffs & Design Decisions:
- **Vite over CRA**: Faster HMR and build times.
- **Client-side State**: Simple management using `useState` or `useReducer` as the app state is mostly transient.

---

### Phase 5 — Scheduled Refresh
#### Module: `.github/workflows/`
- **Trigger**: `0 2 * * *` (2 AM UTC Daily).
- **Workflow**:
  1. Spin up GitHub Runner.
  2. Run `playwright install`.
  3. Execute `main_scraper.py`.
  4. Diff new data against existing ChromaDB collection.
  5. Commit `raw_snapshots/*.json` to the repository (optional versioning).
  6. Re-index changed funds.
- **Secrets**: `GROQ_API_KEY`, `CHROMA_DB_PATH` (if remote).

---

## 📂 Directory Structure

```text
root/
├── Phase1_Scraping/
│   ├── ingestion/           # Scraper, Embedder, Processor
│   └── scraper/             # Playwright browser scripts
├── Phase2_Embedding_Retrieval/
│   └── search/              # ChromaDB retriever wrappers
├── Phase3_Backend_API/
│   └── api/                 # FastAPI (Routes, Models, Core)
├── Phase4_Frontend/
│   └── frontend/            # React (Vite) application
├── Phase5_Scheduled_Refresh/
│   └── .github/             # GitHub Actions Cron Workflows
├── data/
│   ├── raw/                 # JSON snapshots
│   └── chroma/              # Persistent vector db
├── tests/
│   ├── test_api.py          # Endpoints & Scope rejection
│   └── test_rag.py          # Context grounding checks
├── .env.example
├── requirements.txt
└── ARCHITECTURE.md
```

---

## 🛠️ Environment Variables (.env)
| Variable | Description |
| :--- | :--- |
| `GROQ_API_KEY` | API key for llama3-70b-8192 |
| `DATABASE_URL` | Local path or remote ChromaDB endpoint |
| `SCRAPE_INTERVAL` | Hours between scraper runs |
| `LLM_MODEL_ID` | Groq model identifier (llama3-70b-8192) |

---

## 🚀 Future Roadmap
- [ ] Multimodal support (Mutual fund charts).
- [ ] User sessions for longer memory (currently stateless).
- [ ] Integration with more financial sources (Valueresearch/Morningstar).
