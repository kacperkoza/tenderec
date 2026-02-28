# Tenderec Backend

Tender Recommendation Engine — matches Polish public procurement tenders to company profiles using LLM-based scoring and Q&A agent for tender details.

## Quick Start (Docker)

1. Set your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=sk-..." > backend/.env
   ```

2. Build and start all services (from the repo root):
   ```bash
   docker compose up --build -d
   ```

3. Open in browser:
   - http://localhost:3000 — frontend
   - http://localhost:8000/docs — API docs
   - http://localhost:3100 — Langfuse tracing UI (admin@tenderec.local / admin123)

## Run backend app locally

### Prerequisites

- Python 3.12+
- MongoDB running locally (default: `mongodb://localhost:27017`)
- OpenAI API key (set via `OPENAI_API_KEY` env var in `.env`)

```bash
uv run uvicorn main:app --reload --log-level info
```

## Modules

The backend is organized into domain-based modules.

### Companies

Handles company profile management. A company profile is created by sending a free-text description, which the LLM parses into structured data:
- **Industries** the company operates in
- **Service categories** the company offers
- **Target authorities** (e.g., municipalities, road authorities)
- and other not used now, such as: geographical focus, cpv codes, company size.

### Organization Classification

Classifies contracting authorities into 1-3 industries based on their name and tender history. 
Results are cached in MongoDB to avoid repeated LLM calls.

### Recommendations

The core module - scores every tender against a company profile using LLM evaluation and stores the results.
Right now it matches profile to tender name and contracting authority's industries.
Supports filtering by match level and refreshing individual recommendations.

### Tenders

Provides access to a static dataset of ~1,400 Polish public tenders
Also exposes a conversational Q&A agent that can answer natural-language questions about specific tenders, including reading attached PDF/DOCX/TXT documents.

The Q&A agent is built with LangGraph's `create_react_agent` and has access to 7 tools:
- `get_tender_details` — look up a tender by exact name
- `search_tenders` — fuzzy search tenders by name substring
- `list_tenders_by_organization` — filter tenders by contracting organization
- `get_tender_files` — retrieve attached file URLs
- `read_file_content` — download and extract text from PDF/DOCX/TXT (up to 20 MB, 50K chars)
- `get_today_date` — current date for deadline comparison
- `get_company_info` — look up the user's company profile


### Feedback (`src/feedback/`)

Collects user feedback comments per company (e.g., "too short deadline", "not our area"). 
Feedback is incorporated into recommendation prompts to adjust future LLM scoring.

### LLM (`src/llm/`)

Shared LLM infrastructure - OpenAI client and Langfuse tracing client.:

## How the Algorithm Works

### Step 1: Company Profile Extraction

1. User sends a free-text company description  which is extracted by LLM into a structured profile.

Results are stored in MongoDB.
### Step 2: Organization Industry Classification

1. All tenders are loaded from `tenders.json` and classified by LLM.
Results are cached in MongoDB.

### Step 3: Tender Scoring (Core Matching)

1. Build a prompt containing:
   - Company profile (industries, service categories, target authorities)
   - Tender name + contracting organization + organization's classified industries
   - Any user feedback on previously rejected tenders
2. The LLM evaluates:

   **Name Match**: How closely the tender subject matches the company's service categories.

   **Industry Match**: How closely the contracting organization's industries match the company's target authorities.

 Each match also receives a one-sentence reasoning in Polish explaining the score.

### Step 4: Feedback Loop

Users can submit feedback comments per company. On recommendation refresh, these comments are included in the LLM prompt, allowing the model to adjust its scoring based on user preferences (e.g., "we don't bid on contracts under 50k", "too short deadlines").


## Necessary Improvements
- obvious code cleanup - improve readability, write tests, think about structure etc.
- introduces data models for many things that are currently just dicts
- use IDs instead of names for lookups and references
- LLM evaluation for given prompts, input data and output data, eg. profile evaluation, organization classitication, etc.
- Preparing the most important tender data in advance: budgets, obligatory legal requirements, tender details etc
- dont rely only in matching tender on name, company profile, industry, but also on other factors, such as CPV codes, tender size, deadlines, etc.

## LLM
- use structured output
- No LLM evaluation/quality tracking - no tracking of prompt changes or their impact on recommendation quality. No golden dataset or evaluation pipeline to prevent regressions.
- single LLM model used everythere - no differentiation between tasks that might require different levels of reasoning or cost
- each company could have many different profiles
- parse tender documents for richer context - the Q&A agent already has `read_file_content` for PDF/DOCX
- track token usage per company per run, set daily/weekly/montly spend caps
- explore vector/embedding-based retrieval

