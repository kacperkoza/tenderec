from pathlib import Path

from src.classification import constants as classification_constants
from src.llm.service import get_openai_client


SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i klasyfikacji branżowej firm.

Dostajesz listę organizacji (pole "organization") wraz z nazwą przetargu (pole "name") \
z polskich platform przetargowych.

Twoim zadaniem jest:
1. Na podstawie nazwy organizacji i kontekstu z nazwy przetargu — przypisz każdą \
organizację do jednej branży.
2. Użyj zwięzłych, polskich nazw branż (np. "Energetyka", "Górnictwo", \
"Administracja samorządowa", "Transport kolejowy", "Przemysł chemiczny" itp.).
3. Jeśli organizacja pojawia się wielokrotnie (z różnymi przetargami), weź pod uwagę \
WSZYSTKIE konteksty, ale przypisz ją do JEDNEJ branży.
4. Pogrupuj wynik: branża → lista unikalnych organizacji.

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "industries": [
    {
      "industry": "<nazwa branży>",
      "organizations": ["<org1>", "<org2>"]
    }
  ]
}

Nie dodawaj żadnego tekstu poza JSON-em.\
"""


def _load_tenders() -> list[dict]:
    import json
    with open(classification_constants.TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def _build_user_prompt(tenders: list[dict]) -> str:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()

    for t in tenders:
        org = t["metadata"]["organization"]
        name = t["metadata"]["name"]
        key = (org, name)
        if key not in seen:
            seen.add(key)
            lines.append(f"- organization: {org} | name: {name}")

    return f"Oto lista {len(lines)} przetargów (organization + name):\n\n" + "\n".join(lines)


def classify_tenders() -> dict:
    import json

    tenders = _load_tenders()
    client = get_openai_client()
    user_prompt = _build_user_prompt(tenders)

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
    return json.loads(raw)

