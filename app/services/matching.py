import json
from pathlib import Path

from app.services.llm import get_openai_client

COMPANY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "resources"
    / "company"
    / "greenworks_company.md"
)

INDUSTRIES_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "resources"
    / "organization_by_industry"
    / "industries_organizations.json"
)

SYSTEM_PROMPT = """\
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


def _load_company_profile() -> str:
    return COMPANY_PATH.read_text(encoding="utf-8")


def _load_industries() -> list[dict]:
    with open(INDUSTRIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["industries"]


def match_company_to_industries() -> dict:
    """Odczytuje gotową klasyfikację branż i profil firmy, potem pyta LLM o score dopasowania."""
    industries = _load_industries()
    company_profile = _load_company_profile()

    industries_text = json.dumps(industries, ensure_ascii=False, indent=2)

    user_prompt = (
        f"## Profil firmy\n\n{company_profile}\n\n"
        f"## Lista branż z organizacjami\n\n{industries_text}"
    )

    # Krok 4: wyślij do LLM
    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)
    result["company"] = "GreenWorks Infrastructure Ltd."
    return result

