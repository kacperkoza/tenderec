# Tenderec Backend

## Companies

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
- LLM may add additional questions to the company to improve profile quaiality (What size is the company? What certifications do they have? Do they have experience with public tenders?)


## organization classification

multi-level filtering from cheapest to the most expensive, with the following levels:  
- **Level 1: Basic Classification** - Classify organizations into broad categories (e.g., public sector, private sector, non-profit) based on minimal information such as name and description
- level 2: Industry Classification - Classify organizations into specific industries (e.g., healthcare, education, construction) using more detailed information from the description