import json

from src.companies.service import get_company
from src.llm.service import get_openai_client
from src.organization_classification.service import get_industries
from src.recommendations import constants as rec_constants


# classification ideas
"""
1. Kategorie usług
2. Sugerowane Kody CPV
- 
3. Typ Zamawiającego
- Administracja Samorządowa: Urzędy Miast, Gminy, Starostwa.
- Zarządcy Dróg i Transportu: GDDKiA, Zarządy Dróg Miejskich.
- Zarządcy Infrastruktury: PKP PLK (koleje), Lasy Państwowe.

"""


MATCHING_SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i analizy dopasowania firm do branż.

Dostajesz:
1. Profil firmy (opis, usługi, branża).
2. Listę branż wraz z organizacjami, które w nich operują.

Twoim zadaniem jest ocenić, na ile dana firma pasuje do KAŻDEJ z podanych branż \
jako potencjalny dostawca/wykonawca usług.

Dla każdej branży przyznaj score od 0.0 do 1.0:
- 1.0 = idealne dopasowanie
- 0.7-0.9 = wysokie dopasowanie
- 0.4-0.6 = częściowe dopasowanie
- 0.1-0.3 = niskie dopasowanie
- 0.0 = brak dopasowania

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

TENDER_SCORING_SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych.

Dostajesz profil firmy oraz listę przetargów. Każdy przetarg zawiera:
- id: unikalny identyfikator
- name: nazwa przetargu
- organization: zamawiający
- industry: branża zamawiającego

Dla KAŻDEGO przetargu oceń:

1. score (0.0-1.0): Jak bardzo przetarg pasuje do firmy?
   - Weź pod uwagę ZARÓWNO dopasowanie do branży zamawiającego JAK I treść nazwy przetargu.
   - Nazwa przetargu jest ważniejsza — firma zieleni nie powinna dostawać 1.0 za przetarg IT w gminie.
   - 1.0 = nazwa przetargu idealnie opisuje usługi firmy
   - 0.7-0.9 = przetarg prawdopodobnie dotyczy usług firmy
   - 0.4-0.6 = możliwe częściowe dopasowanie
   - 0.1-0.3 = branża pasuje, ale nazwa przetargu nie
   - 0.0 = brak dopasowania

2. reasoning: Krótkie uzasadnienie po polsku (1-2 zdania). Odnieś się do nazwy przetargu I branży.

3. tender_size: Rozmiar przetargu na podstawie nazwy i kontekstu:
   - "duży" = duże inwestycje (budowa drogi, budynku, infrastruktury, rewitalizacja terenu, wieloletnie umowy)
   - "średni" = usługi cykliczne, utrzymanie, serwis, dostawy o średniej wartości
   - "mały" = jednorazowe dostawy, drobne zakupy, akcesoria, materiały biurowe

Odpowiedz WYŁĄCZNIE poprawnym JSON-em:
{
  "results": [
    {
      "id": <int>,
      "score": <float 0.0-1.0>,
      "reasoning": "<uzasadnienie po polsku>",
      "tender_size": "mały" | "średni" | "duży"
    }
  ]
}

Nie dodawaj żadnego tekstu poza JSON-em.\
"""


async def _load_company_profile(company_name: str) -> str:
    company = await get_company(company_name)
    return json.dumps(company["profile"], ensure_ascii=False, indent=2)


def _load_industries_list() -> list[dict]:
    data = get_industries()
    return data["organizations"]


def _load_org_to_industry_map() -> dict[str, list[str]]:
    from src.organization_classification.service import _load_from_file

    data = _load_from_file()
    org_map: dict[str, list[str]] = {}
    for entry in data["organizations"]:
        org_map[entry["organization"]] = entry["industries"]
    return org_map


def _load_tenders() -> list[dict]:
    with open(rec_constants.TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def _score_tenders_via_llm(
    company_profile: str, tenders_with_industry: list[dict]
) -> list[dict]:
    """Send all tenders to LLM in one call for per-tender scoring and size classification."""
    client = get_openai_client()

    tender_lines = "\n".join(
        f'{{"id": {i}, "name": "{t["name"]}", "organization": "{t["organization"]}", "industry": "{t["industry"]}"}}'
        for i, t in enumerate(tenders_with_industry)
    )

    user_prompt = (
        f"## Profil firmy\n\n{company_profile}\n\n"
        f"## Przetargi do oceny\n\n{tender_lines}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": TENDER_SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(response.choices[0].message.content)["results"]


async def match_company_to_industries(company_name: str) -> dict:
    industries = _load_industries_list()
    company_profile = await _load_company_profile(company_name)
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

    result = json.loads(response.choices[0].message.content)  # type: ignore[arg-type]
    result["company"] = company_name
    return result


async def get_recommendations(
    company_name: str, threshold: float = rec_constants.SCORE_THRESHOLD
) -> dict:
    # 1. Build org -> industries map from file (fast)
    org_to_industries = _load_org_to_industry_map()

    # 2. Load tenders and attach industries to each
    tenders = _load_tenders()
    tenders_with_industry = [
        {
            "tender_url": t["tender_url"],
            "name": t["metadata"]["name"],
            "organization": t["metadata"]["organization"],
            "industry": ", ".join(
                org_to_industries.get(t["metadata"]["organization"], ["Nieznana"])
            ),
        }
        for t in tenders
    ]

    # 3. Load company profile from MongoDB
    company_profile = await _load_company_profile(company_name)

    # 4. Send to LLM for per-tender scoring
    scored = _score_tenders_via_llm(company_profile, tenders_with_industry)

    # 5. Merge scores back and filter by threshold
    recommendations = []
    for item in scored:
        i = item["id"]
        score = item["score"]
        if score < threshold:
            continue
        t = tenders_with_industry[i]
        recommendations.append(
            {
                "tender_url": t["tender_url"],
                "name": t["name"],
                "organization": t["organization"],
                "industry": t["industry"],
                "score": score,
                "reasoning": item["reasoning"],
                "tender_size": item["tender_size"],
            }
        )

    recommendations.sort(key=lambda x: (-x["score"], x["name"]))

    return {
        "company_name": company_name,
        "threshold": threshold,
        "total": len(recommendations),
        "recommendations": recommendations,
    }
