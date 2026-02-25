import json
from datetime import datetime

from src.config import settings
from src.llm.service import get_openai_client
from src.organization_classification import constants


SYSTEM_PROMPT = """\
Jesteś ekspertem od polskiego rynku zamówień publicznych i klasyfikacji branżowej organizacji.

Dostajesz listę organizacji (pole "organization") wraz z nazwą przetargu (pole "name") \
z polskich platform przetargowych.

Twoim zadaniem jest:
1. Na podstawie nazwy organizacji i kontekstu z nazwy przetargu — przypisz każdą \
organizację do DOKŁADNIE 3 branż (top 3, od najbardziej pasującej).
2. Użyj zwięzłych, polskich nazw branż (np. "Energetyka", "Górnictwo", \
"Administracja samorządowa", "Transport kolejowy", "Przemysł chemiczny" itp.).
3. Jeśli organizacja pojawia się wielokrotnie (z różnymi przetargami), weź pod uwagę \
WSZYSTKIE konteksty.
4. Pierwsza branża na liście = najbardziej trafna, trzecia = najmniej trafna z top 3. Możesz zwrócić mniej niż 3 branże, jeśli nie jesteś pewien, ale NIE ZWRACAJ WIĘCEJ NIŻ 3.

Odpowiedz WYŁĄCZNIE poprawnym JSON-em w formacie:
{
  "organizations": [
    {
      "organization": "<nazwa organizacji>",
      "industries": ["<branża 1 - najlepsza>", "<branża 2>", "<branża 3>"]
    }
  ]
}

Nie dodawaj żadnego tekstu poza JSON-em.\
"""


def _load_tenders() -> list[dict]:
    with open(constants.TENDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tenders"]


def _filter_by_deadline(tenders: list[dict]) -> list[dict]:
    today = constants.TODAY
    result = []
    for t in tenders:
        deadline_str = t["metadata"]["submission_deadline"]
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M").date()
        except ValueError:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S").date()
        if deadline > today:
            result.append(t)
    return result


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

    return f"Oto lista {len(lines)} przetargów (organization + name):\n\n" + "\n".join(
        lines
    )


def _save_result(result: dict) -> None:
    output_path = constants.INDUSTRIES_OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def _load_from_file() -> dict:
    with open(constants.INDUSTRIES_OUTPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _classify_via_llm() -> dict:
    all_tenders = _load_tenders()
    tenders = _filter_by_deadline(all_tenders)

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
    result = json.loads(raw)  # type: ignore[arg-type]

    _save_result(result)

    return result


def get_industries() -> dict:
    """
    Zwraca klasyfikację organizacji wg branż (top 3 per organizacja).

    Źródło danych zależy od ustawienia ORGANIZATION_CLASSIFICATION_SOURCE:
    - "file" → odczytuje z organizations_by_industry.json (szybko, bez kosztu LLM)
    - "llm"  → klasyfikuje na żywo przez LLM (wolno, zużywa tokeny)
    """
    source = settings.organization_classification_source

    if source == "file":
        return _load_from_file()
    else:
        return _classify_via_llm()
