"""
Skrypt klasyfikujący organizacje z tenders_sublist.json wg branży
na podstawie nazwy organizacji.
"""
import json
from collections import defaultdict

# Reguły klasyfikacji: (frazy do szukania w nazwie org) -> branża
RULES = [
    # Energetyka / Paliwa / Rafineria
    (["TAURON"], "Energetyka"),
    (["Energa"], "Energetyka"),
    (["PGE"], "Energetyka"),
    (["ORLEN"], "Energetyka / Paliwa"),
    (["WĘGLOKOKS ENERGIA", "Węglokoks Energia"], "Energetyka"),

    # Górnictwo
    (["KGHM", "Centrum Zaopatrzenia Budownictwa Lubin", "Zespół Asortymentu", "Zespół Towarów Strategicznych", "Zespół Środków Ochrony"], "Górnictwo (KGHM)"),
    (["Węgiel Bogdanka", "WĘGIEL BOGDANKA", "BOGDANKA"], "Górnictwo węglowe"),
    (["Kopalnia Węgla Brunatnego", "KWB Konin", "PAK Kopalnia"], "Górnictwo węglowe"),

    # Chemia
    (["Grupa Azoty"], "Przemysł chemiczny"),

    # Hutnictwo / Metalurgia
    (["Alchemia"], "Hutnictwo / Metalurgia"),
    (["Cognor", "COGNOR"], "Hutnictwo / Metalurgia"),
    (["JSW KOKS", "JSW Koks"], "Koksownictwo"),
    (["Tokai Cobex", "TOKAI COBEX"], "Hutnictwo / Metalurgia (elektrody grafitowe)"),

    # Transport kolejowy
    (["PKP CARGO"], "Transport kolejowy"),
    (["PKP INTERCITY"], "Transport kolejowy"),

    # Transport miejski
    (["Miejskie Przedsiębiorstwo Komunikacyjne", "MPK"], "Transport miejski"),
    (["Transgór", "TRANSGÓR"], "Transport miejski"),

    # Wodociągi / Kanalizacja
    (["Wodociągów i Kanalizacji", "MPWiK"], "Gospodarka wodno-kanalizacyjna"),

    # Farmacja / Dystrybucja farmaceutyczna
    (["FARMACOL"], "Dystrybucja farmaceutyczna"),

    # Służba zdrowia
    (["Szpital", "SZPITAL"], "Służba zdrowia"),
    (["Zakład Opieki Zdrowotnej", "SPZOZ", "SP ZOZ", "Opieki Zdrowotnej"], "Służba zdrowia"),
    (["CENTRUM MEDYCZNE", "Centrum Medyczne"], "Służba zdrowia"),
    (["Krwiodawstwa"], "Służba zdrowia"),
    (["sprzęt medyczny", "Woliński"], "Służba zdrowia (prywatna praktyka)"),
    (["Nadir II"], "Usługi zdrowotne / Opieka senioralna"),

    # Służba więzienna / Wymiar sprawiedliwości
    (["Areszt Śledczy"], "Służba więzienna"),
    (["Zakład Karny"], "Służba więzienna"),
    (["Sąd Rejonowy"], "Wymiar sprawiedliwości"),

    # Wojsko / Obronność
    (["Wojskowy Oddział Gospodarczy", "WOG", "24WOG"], "Wojsko / Obronność"),

    # Administracja publiczna / Samorządy
    (["Gmina ", "GMINA "], "Administracja samorządowa (gmina)"),
    (["Powiat "], "Administracja samorządowa (powiat)"),
    (["Miasto Ł", "Miasto "], "Administracja samorządowa (miasto)"),
    (["Województwo ", "Wojewódz", "Urząd Marszałkowski"], "Administracja samorządowa (województwo)"),
    (["Urząd Miejski"], "Administracja samorządowa (miasto)"),
    (["Urząd Pracy"], "Administracja publiczna (urząd pracy)"),
    (["Zarząd Dróg", "Zarząd Drg"], "Infrastruktura drogowa (samorząd)"),
    (["Zarząd Budynków Miejskich", "Towarzystwa Budownictwa Społecznego"], "Gospodarka nieruchomościami (samorząd)"),
    (["Ośrodek Polityki Społecznej"], "Pomoc społeczna (samorząd)"),
    (["Stalowowolskie Centrum Usług"], "Administracja samorządowa (centrum usług wspólnych)"),
    (["Olsztyn"], "Administracja publiczna (ZUS)"),  # ZUS Olsztyn
    (["Samtgemeinde"], "Administracja samorządowa (Niemcy)"),
    (["Park Przemysłowy"], "Infrastruktura przemysłowa (samorząd)"),

    # Edukacja
    (["Szkoła Podstawowa", "SZKOŁA PODSTAWOWA"], "Edukacja (szkoła)"),
    (["Centrum Edukacji Rolniczej"], "Edukacja (rolnicza)"),
    (["Centrum Rozwoju Edukacji"], "Edukacja"),
    (["Zakład Doskonalenia Zawodowego"], "Edukacja / Szkolenia zawodowe"),
    (["OŚRODEK DORADZTWA ROLNICZEGO", "Ośrodek Doradztwa"], "Doradztwo rolnicze"),

    # Fundacje / NGO
    (["Fundacja"], "Organizacja pozarządowa / Fundacja"),

    # IT / Technologia
    (["Pixel Technology"], "IT / Technologia"),

    # Budownictwo / Produkcja przemysłowa
    (["ZPUE"], "Produkcja urządzeń elektroenergetycznych"),
    (["Pekabex"], "Budownictwo (prefabrykaty betonowe)"),
    (["Cersanit"], "Produkcja ceramiki / Wyposażenie łazienek"),
    (["LEONI KABEL"], "Produkcja kabli / Motoryzacja"),
    (["Przedsiębiorstwo Techniczne Plex"], "Produkcja przemysłowa"),

    # Spożywcza / Rolnictwo
    (["GOODVALLEY"], "Przemysł spożywczy (mięsny)"),
    (["Agri Plus", "Oddział Paszowy"], "Przemysł paszowy / Rolnictwo"),
    (["BZK I WSPÓLNICY", "BZK I WSPLNICY", "Komagra"], "Przemysł spożywczy"),

    # Leśnictwo
    (["Nadleśnictwo"], "Leśnictwo"),

    # Sport / Usługi
    (["SNOW DREAM"], "Sport / Rekreacja"),
]


def classify(org_name: str) -> str:
    for keywords, industry in RULES:
        for kw in keywords:
            if kw.lower() in org_name.lower():
                return industry
    return "Nieokreślona"


def main():
    with open("resources/tender/tenders_sublist.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Zbierz unikalne organizacje
    orgs = sorted({t["metadata"]["organization"] for t in data["tenders"]})

    # Klasyfikacja
    org_industry = {org: classify(org) for org in orgs}

    # Grupowanie branża -> lista organizacji
    by_industry = defaultdict(list)
    for org, ind in sorted(org_industry.items(), key=lambda x: x[1]):
        by_industry[ind].append(org)

    # Wypisz
    print("=" * 70)
    print(f"KLASYFIKACJA {len(orgs)} ORGANIZACJI WG BRANŻY")
    print("=" * 70)
    for industry in sorted(by_industry):
        org_list = by_industry[industry]
        print(f"\n🏷  {industry} ({len(org_list)} org.):")
        for o in org_list:
            print(f"    • {o}")

    # Zapisz wynik do JSON
    output = {
        "total_organizations": len(orgs),
        "total_industries": len(by_industry),
        "by_industry": {k: sorted(v) for k, v in sorted(by_industry.items())},
        "organization_to_industry": org_industry,
    }
    out_path = "resources/organization_by_industry/organizations_by_industry.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Zapisano do {out_path}")


if __name__ == "__main__":
    main()

