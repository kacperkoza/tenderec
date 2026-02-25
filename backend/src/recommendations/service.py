import json

from src.llm.service import get_openai_client
from src.organization_classification.service import get_industries
from src.recommendations import constants as rec_constants


MATCHING_SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i analizy dopasowania firm do branż.

Dostajesz:
1. Profil firmy (opis, usługi, branża).
2. Listę branż wraz z organizacjami, które w nich operują.

Twoim zadaniem jest ocenić, na ile dana firma pasuje do KAŻDEJ z podanych branż \
jako potencjalny dostawca/wykonawca usług.

Dla każdej branży przyznaj score od 0.0 do 1.0:
- 1.0 = idealne dopasowanie (firma świadczy dokładnie takie usługi, jakich potrzebują organizacje z tej branży)
- 0.7-0.9 = wysokie dopasowanie (duże prawdopodobieństwo, że firma może realizować zamówienia)
- 0.4-0.6 = częściowe dopasowanie (firma mogłaby realizować niektóre zamówienia)
- 0.1-0.3 = niskie dopasowanie (marginalne szanse)
- 0.0 = brak dopasowania

Weź pod uwagę:
- Czy organizacje z danej branży mogą potrzebować usług opisanych w profilu firmy?
- Czy firma ma kompetencje do realizacji typowych zamówień w tej branży?
- Czy jest realne, że firma startowałaby w przetargach ogłaszanych przez te organizacje?

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "matches": [
    {
      "industry": "<nazwa branży>",
      "score": <float 0.0-1.0>,
      "reasoning": "<krótkie uzasadnienie po polsku>"
    }
  ]
}

Posortuj wynik od najwyższego score do najniższego.
Nie dodawaj żadnego tekstu poza JSON-em.\
"""


def _load_company_profile(company_id: str) -> str:
    path = rec_constants.COMPANY_DIR / f"{company_id}.md"
    return path.read_text(encoding="utf-8")


def _load_industries_list() -> list[dict]:
    return get_industries()["industries"]


def _load_org_to_industry_map() -> dict[str, str]:
    industries = _load_industries_list()
    org_map: dict[str, str] = {}
    for group in industries:
        for org in group["organizations"]:
            org_map[org] = group["industry"]
    return org_map


def _load_tenders() -> list[dict]:
    with open(rec_constants.TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def match_company_to_industries(company_id: str) -> dict:
    industries = _load_industries_list()
    company_profile = _load_company_profile(company_id)
    industries_text = json.dumps(industries, ensure_ascii=False, indent=2)

    user_prompt = (
        f"## Profil firmy\n\n{company_profile}\n\n"
        f"## Lista branż z organizacjami\n\n{industries_text}"
    )

    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": MATCHING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    result = json.loads(response.choices[0].message.content)
    company_name = rec_constants.COMPANY_REGISTRY.get(company_id, company_id)
    result["company"] = company_name
    return result


def get_recommendations(company_id: str, threshold: float = rec_constants.SCORE_THRESHOLD) -> dict:
    company_name = rec_constants.COMPANY_REGISTRY.get(company_id)
    if not company_name:
        raise ValueError(f"Unknown company_id: {company_id}")

    match_result = match_company_to_industries(company_id)

    relevant_industries: dict[str, dict] = {
        m["industry"]: m
        for m in match_result["matches"]
        if m["score"] >= threshold
    }

    if not relevant_industries:
        return {
            "company_id": company_id,
            "company": company_name,
            "threshold": threshold,
            "total": 0,
            "recommendations": [],
        }

    org_to_industry = _load_org_to_industry_map()
    tenders = _load_tenders()
    recommendations = []

    for tender in tenders:
        org = tender["metadata"]["organization"]
        industry = org_to_industry.get(org)
        if not industry or industry not in relevant_industries:
            continue

        match = relevant_industries[industry]
        recommendations.append({
            "tender_url": tender["tender_url"],
            "name": tender["metadata"]["name"],
            "organization": org,
            "industry": industry,
            "score": match["score"],
            "reasoning": match["reasoning"],
        })

    recommendations.sort(key=lambda x: (-x["score"], x["name"]))

    return {
        "company_id": company_id,
        "company": company_name,
        "threshold": threshold,
        "total": len(recommendations),
        "recommendations": recommendations,
    }

