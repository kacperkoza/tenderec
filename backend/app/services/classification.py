import json
from pathlib import Path

from app.services.llm import get_openai_client

TENDERS_PATH = Path(__file__).resolve().parent.parent.parent / "resources" / "tender" / "tenders_sublist.json"

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


def load_tenders() -> list[dict]:
    with open(TENDERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["tenders"]


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

    header = f"Oto lista {len(lines)} przetargów (organization + name):\n\n"
    return header + "\n".join(lines)


def classify_tenders() -> dict:
    """Wysyła organizacje z przetargów do LLM i zwraca pogrupowane branże."""
    tenders = load_tenders()
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

