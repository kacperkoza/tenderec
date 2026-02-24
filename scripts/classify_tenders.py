"""
Skrypt wysyłający organizacje z tenders_sublist.json do LLM
w celu pogrupowania ich wg branż.

Użycie:
    python -m scripts.classify_tenders
lub:
    cd <project_root> && python scripts/classify_tenders.py
"""

import json
import sys
from pathlib import Path

# Dodaj root projektu do sys.path, żeby importy z app/ działały
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.llm import get_openai_client

TENDERS_PATH = Path(__file__).resolve().parent.parent / "resources" / "tender" / "tenders_sublist.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "resources" / "organization_by_industry" / "organizations_by_industry.json"

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


def build_user_prompt(tenders: list[dict]) -> str:
    """Buduje prompt z listą par (organization, name) z przetargów."""
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


def classify(tenders: list[dict]) -> dict:
    client = get_openai_client()

    user_prompt = build_user_prompt(tenders)
    print(f"📤 Wysyłam {len(user_prompt)} znaków do LLM...")

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

    print(f"✅ Odpowiedź: {response.usage.prompt_tokens} prompt tokens, "
          f"{response.usage.completion_tokens} completion tokens")

    return result


def main():
    tenders = load_tenders()
    print(f"📂 Załadowano {len(tenders)} przetargów z {TENDERS_PATH.name}")

    result = classify(tenders)

    # Wyświetl
    for group in result["industries"]:
        industry = group["industry"]
        orgs = group["organizations"]
        print(f"\n🏷  {industry} ({len(orgs)} org.):")
        for org in orgs:
            print(f"    • {org}")

    # Zapisz
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Zapisano wynik do {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

