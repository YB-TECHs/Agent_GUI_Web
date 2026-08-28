"""
Module fetch_corpus.py.
"""

import wikipediaapi
from pathlib import Path

# Dossier de destination du corpus brut
OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Liste des pages Wikipédia à récupérer (thème : microfinance au Cameroun)
# Les titres doivent correspondre exactement au titre de la page Wikipédia FR.
PAGES = [
    "Microfinance",
    "Microcrédit",
    "Tontine",
    "Finance solidaire",
    "Système bancaire",
]

# User-agent requis par l'API Wikipédia (bonne pratique, évite d'être bloqué)
USER_AGENT = "Stage-RAG-Microfinance-Cameroun/1.0 (contact: etudiant@example.com)"


def fetch_page(wiki, title: str) -> str | None:
    """Récupère le texte complet d'une page Wikipédia par son titre."""
    page = wiki.page(title)
    if not page.exists():
        return None
    return page.text


def slugify(title: str) -> str:
    """Transforme un titre en nom de fichier propre."""
    return title.lower().replace(" ", "_").replace("'", "").replace("é", "e").replace("è", "e")


def main():
    wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language="fr")

    reussies = []
    echouees = []

    for title in PAGES:
        print(f"Récupération : {title} ...", end=" ")
        text = fetch_page(wiki, title)
        if text is None or len(text.strip()) == 0:
            print("ÉCHEC (page introuvable ou vide)")
            echouees.append(title)
            continue

        filename = OUTPUT_DIR / f"{slugify(title)}.txt"
        filename.write_text(text, encoding="utf-8")
        print(f"OK ({len(text)} caractères) -> {filename}")
        reussies.append(title)

    print("\n--- Résumé ---")
    print(f"Pages récupérées avec succès : {len(reussies)}")
    for t in reussies:
        print(f"  - {t}")
    if echouees:
        print(f"\nPages en échec (à vérifier manuellement) : {len(echouees)}")
        for t in echouees:
            print(f"  - {t}")


if __name__ == "__main__":
    main()
