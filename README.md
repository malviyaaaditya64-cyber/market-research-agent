# Autonomous Market Research Agent

A multi-agent system that automates market research, generates data‑driven reports, and provides LLM‑hallucination detection via a CriticAgent.

**One‑line description:** An end‑to‑end pipeline that scrapes Wikipedia, synthesizes findings with Google Gemini, and produces a polished report while flagging unsupported claims.

---

## Architecture

The core is a **five‑agent pipeline** that passes context through a shared in‑memory store:

1. **ResearchAgent** – Queries Wikipedia for topic‑specific data and stores raw snippets in SharedMemory.
2. **SharedMemory** – Lightweight key‑value store (SQLite‑backed) that decouples agents and preserves query context.
3. **AnalysisAgent** – Reads the collected research, structures insights, and drafts a report outline.
4. **WriterAgent** – Expands the outline into a full markdown report, citing sources from SharedMemory.
5. **CriticAgent** – Re‑reads the generated report, cross‑checks every claim against the original research data, and flags any unsupported statements (hallucination detection).

**Key differentiator:** The **self‑critique/gap‑detect loop** – after the WriterAgent finishes, the CriticAgent returns feedback; if gaps are found, the pipeline can re‑run WriterAgent with refined prompts until all claims are validated. This iterative guardrail is what sets the project apart from static LLM generators.

---

## Tech Stack

- **Backend:** Python, FastAPI
- **LLM:** Google Gemini API (via `google-generativeai`)
- **Database:** SQLite (for SharedMemory and persistent metadata)
- **Frontend:** Vanilla HTML/CSS/JS (no framework, served static)
- **Agent Framework:** Custom async orchestration (no LangChain)

---

## Setup Instructions

```powershell
# 1️⃣ Clone the repo
git clone https://github.com/your-username/market_research_agent.git
cd market_research_agent

# 2️⃣ Install dependencies
pip install -r requirements.txt

# 3️⃣ Create .env file
# Get a key from: https://aistudio.google.com/app/apikey
echo "GEMINI_API_KEY=your_key_here" > .env

# 4️⃣ Run the backend
uvicorn api:app --reload --port 8000

# 5️⃣ Serve the frontend (from the ./frontend folder)
python -m http.server 5500
```

---

## Usage

1. Open `http://localhost:5500` in your browser.  
2. Enter a research topic (e.g., "AI trends 2024") and click **Run Research**.  
3. The frontend sends the query to the FastAPI backend (`/api/research`).  
4. The multi‑agent pipeline runs; results appear on screen after the CriticAgent validation.  
5. Download the generated report or trigger a new query.

---

## Key Feature Highlight

**CriticAgent Hallucination Detection** – The CriticAgent systematically compares each claim in the generated report against the source snippets stored in SharedMemory. Any statement that cannot be directly supported is flagged with a red banner and the original source excerpt is shown. This LLM‑hallucination guardrail ensures the final output is grounded in actual research data, not invented facts.

---

## Limitations

- **Research source:** Currently limited to Wikipedia scraping; no real‑time web crawling or paid APIs.  
- **Rate limits:** Gemini free‑tier constraints may throttle high‑frequency requests.  
- **No invented research:** The design choice to let the CriticAgent flag gaps means that if the source data is insufficient, the report will explicitly note missing information rather than hallucinating filler.

---

## Future Improvements

- **Multi‑source research:** Integrate news APIs (e.g., NewsAPI, Google Search) alongside Wikipedia.  
- **Deployment:** Dockerize the backend and host on Cloud Run / Render.  
- **Authentication:** Add API‑key or OAuth protection for the `/api/research` endpoint.  
- **Caching:** Persist validated reports to avoid re‑processing identical queries.  
- **UI enhancements:** Real‑time pipeline status, interactive claim graph, and export to PDF.