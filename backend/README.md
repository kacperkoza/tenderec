# Tenderec Backend

Tender Recommendation Engine — matches Polish public procurement tenders to company profiles using LLM scoring.

## Prerequisites

- Python 3.12+
- MongoDB running locally (default: `mongodb://localhost:27017`)
- OpenAI API key (set via `OPENAI_API_KEY` env var in `.env`)

## Setup

```bash
uv sync --all-extras
```

Set your OpenAI API key in the `.env` file:

```
OPENAI_API_KEY=sk-...
```

Optional `.env` overrides:

```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=tenderec
LLM_MODEL=gpt-4o-mini
ORGANIZATION_CLASSIFICATION_SOURCE=mongodb
TENDER_DEADLINE_DATE=2026-01-10
```

## Running the app

```bash
fastapi dev main.py
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Running tests

```bash
uv run pytest tests/ -v
```

Tests mock both MongoDB and the OpenAI client — no running database or API token required.

## API Endpoints

### Companies

The companies module handles company profile management. 
A company profile is created by sending a free-text description to `PUT /api/v1/companies/{company_name}`. 
The LLM extracts structured information from the description: 
- industries, 
- service categories, 
- CPV codes, 
- target authorities
- geography. 

- All extracted values are in Polish. 
The result is stored in MongoDB for further use in tender search and matching.

To retrieve a saved profile use `GET /api/v1/companies/{company_name}`.

### Example

```bash
curl -X PUT "http://localhost:8000/api/v1/companies/greenworks" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "GreenWorks Infrastructure Ltd. is a mid-sized environmental services company specializing in the development, maintenance, and revitalization of green areas. The company delivers end-to-end services related to urban greenery, public parks, roadside vegetation, and municipal green infrastructure. GreenWorks works primarily with public sector clients, including municipalities, road authorities, public institutions, and state-owned entities. Core services: maintenance of public green areas, tree cutting and removal, new plantings, landscaping projects, seasonal vegetation management, roadside and railway greenery. Geographic focus: Poland."
  }'
```
```bash
curl -X GET "http://localhost:8000/api/v1/companies/greenworks" \
  -H "Content-Type: application/json" | jq
```
Result: 
```json
{
  "company_name": "greenworks",
  "profile": {
    "company_info": {
      "name": "GreenWorks Infrastructure Ltd.",
      "industries": [
        "usługi środowiskowe",
        "utrzymanie terenów zielonych",
        "architektura krajobrazu"
      ]
    },
    "matching_criteria": {
      "service_categories": [
        "utrzymanie terenów zielonych",
        "wycinka drzew",
        "nasadzenia roślin",
        "rewitalizacja terenów zielonych",
        "zarządzanie sezonową roślinnością",
        "prace związane z zielenią przy drogach i infrastrukturze publicznej"
      ],
      "cpv_codes": [
        "77310000-6",
        "77340000-5",
        "45112710-5",
        "45112700-2",
        "77314100-5"
      ],
      "target_authorities": [
        "gminy",
        "zarządy dróg",
        "instytucje publiczne",
        "jednostki państwowe"
      ],
      "geography": {
        "primary_country": "Polska"
      }
    }
  },
  "created_at": "2026-02-25T15:02:00.478000"
}
```

**Later improvements may include:**
- Support for multiple profiles per company (e.g., different service lines)
- More detailed geographic targeting (e.g., specific regions or cities)
- Additional structured data extraction (e.g., company size, certifications)
- LLM may add additional questions to the company to improve profile quality (What size is the company? What certifications do they have? Do they have experience with public tenders?)


### Organization Classification

`GET /api/v1/organizations/industries` classifies contracting authorities into 2-3 industries each, based on their name and tender history.

- Default source: `mongodb` (reads cached results, no LLM cost)
- Set `ORGANIZATION_CLASSIFICATION_SOURCE=llm` to reclassify via LLM and save to MongoDB
- Organizations are classified in batches of 80 per LLM call
- Only tenders with deadlines after the reference date are included

```bash
curl -X GET "http://localhost:8000/api/v1/organizations/industries" | jq
```

## Limitations

- Rate limits depend on your OpenAI plan — classification of organizations requires multiple batches

## TODO:
- tests: evaluate LLM results

## Future vision
- use vector databases for more efficient tender retrieval and matching without LLM scoring of all tenders
- point places in documents that confirm LLM reasoning (e.g., "LLM says this tender matches because of CPV code 77310000-6, which corresponds to maintenance of green areas. The tender includes this CPV code in its metadata.")