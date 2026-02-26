# Tenderec Backend

Tender Recommendation Engine — matches Polish public procurement tenders to company profiles using LLM-based two-axis scoring.

## Prerequisites

- Python 3.12+
- MongoDB running locally (default: `mongodb://localhost:27017`)
- OpenAI API key (set via `OPENAI_API_KEY` env var in `.env`)

## Run app

```bash
uv run uvicorn main:app --reload --log-level info
```
and visit `http://localhost:8000/docs` for interactive API documentation.

## Running tests


## Modules

The backend is organized into domain-based modules.

### Companies (`src/companies/`)

Handles company profile management. A company profile is created by sending a free-text description, which the LLM parses into structured data:
- **Industries** the company operates in
- **Service categories** the company offers
- **CPV codes** (Common Procurement Vocabulary) - not used now
- **Target authorities** (e.g., municipalities, road authorities)
- **Geography** (primary country) - not used now

### Organization Classification (`src/organization_classification/`)

Classifies contracting authorities into 1-3 industries based on their name and tender history. 
Results are cached in MongoDB to avoid repeated LLM calls.

### Recommendations (`src/recommendations/`)

The core module - scores every tender against a company profile using LLM evaluation and stores the results.
Right now it matches profile to tender name and contracting authority's industries.
Supports filtering by match level and refreshing individual recommendations.

### Tenders (`src/tenders/`)

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

   **Industry Match**: How closely the contracting organization's industries match the company's target industries/authorities.

 Each match also receives a one-sentence reasoning in Polish explaining the score.

### Step 4: Feedback Loop

Users can submit feedback comments per company. On recommendation refresh, these comments are included in the LLM prompt, allowing the model to adjust its scoring based on user preferences (e.g., "we don't bid on contracts under 50k", "too short deadlines").

## Limitations




### LLM-Related
- **Rate limits**: Scoring all 1,412 tenders requires many parallel API calls. Throughput depends on your OpenAI plan tier. The semaphore is set to 5 concurrent requests.
- **Cost**: Full recommendation generation for one company scores every tender individually via the LLM. With GPT-4o-mini this is affordable but not free.
- **Consistency**: Despite `temperature=0.2`, LLM outputs are not fully deterministic. Re-running the same scoring may produce slightly different results.
- **Hallucination risk**: The LLM may misclassify tenders or organizations, especially for ambiguous or niche domains.

### Data-Related
- **Static tender dataset**: Tenders are loaded from a fixed JSON file (`tenders.json`), not from a live scraping pipeline. The data represents a snapshot from `platformazakupowa.pl` around 2026-01-07.
- **Single source**: Only tenders from `platformazakupowa.pl` are included. Other Polish procurement platforms (e.g., TED, BZP) are not covered.
- **Polish only**: All LLM prompts, extracted profiles, and reasoning are in Polish. The system does not support other languages.

### Architecture-Related
- **No vector search**: Every tender is scored individually by the LLM — there is no pre-filtering via embeddings or vector similarity. This makes full scoring slow and expensive.
- **Single company profile**: Each company has one profile. Companies with multiple distinct service lines cannot represent them separately.
- **No authentication**: The API has no auth layer — anyone with access can read/write any company's data.
- **No pagination**: Recommendation and tender list endpoints return all results at once.

---

## Future Improvements

### Short-Term
- **LLM evaluation tests**: Automated evaluation of LLM output quality (are recommendations actually relevant?)
- **Token and cost tracking**: Count tokens used and cost per endpoint call
- **Structured output**: Use OpenAI structured output / function calling instead of parsing free-text JSON from the LLM
- **Pagination**: Add pagination to recommendation and tender list endpoints
- **Authentication**: Add API key or JWT-based authentication

### Medium-Term
- **Vector database pre-filtering**: Use embeddings (e.g., in Qdrant or Pinecone) to pre-filter tenders by semantic similarity before LLM scoring. This would eliminate the need to score all 1,412 tenders individually.
- **Live tender ingestion**: Replace the static JSON file with a scraping pipeline that pulls new tenders from `platformazakupowa.pl` (and potentially other sources) on a schedule.
- **Multiple company profiles**: Support multiple profiles per company for different service lines or business divisions.
- **Richer company profiling**: Extract additional structured data (company size, certifications, past tender experience) and allow the LLM to ask follow-up questions to improve profile quality.
- **Document-grounded reasoning**: Point to specific places in tender documents that confirm LLM reasoning (e.g., "this tender matches because the specification on page 3 lists CPV code 77310000-6").

### Long-Term Vision
- **Orchestrator agent architecture**: Replace the monolithic scoring pipeline with an orchestrator agent that delegates to specialized sub-agents (profile extraction agent, tender retrieval agent, matching explanation agent).
- **Multi-source aggregation**: Aggregate tenders from multiple Polish and EU procurement platforms (TED, BZP, platformazakupowa.pl).
- **Learning from feedback**: Use accumulated user feedback to fine-tune scoring or train a lightweight classifier that pre-filters before LLM evaluation.
- **Notification system**: Proactively notify companies when new tenders matching their profile appear.

---
