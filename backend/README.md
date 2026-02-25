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
