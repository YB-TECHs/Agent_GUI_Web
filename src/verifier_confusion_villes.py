"""
Module verifier_confusion_villes.py.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from rag_agent import supprimer_accents

FICHIER_S2 = Path("data/processed/resultats_tests_S2.csv")
FICHIER_S3 = Path("data/processed/dataset_interactions_S3.csv")
FICHIER_RAPPORT = Path("data/processed/rapport_confusion_villes.csv")

# Meme liste que celle utilisee pour la generation des questions
# (generer_questions_dataset.py), pour rester coherent.
VILLES_CANDIDATES = [
    "Yaounde", "Douala", "Bafoussam", "Bamenda", "Garoua", "Maroua",
    "Ngaoundere", "Bertoua", "Ebolowa", "Buea", "Limbe", "Kribi", "Edea",
    "Foumban", "Dschang", "Kumba", "Nkongsamba", "Sangmelima", "Bafia",
    "Mbalmayo", "Meiganga", "Guider", "Mokolo", "Koussere", "Mora",
    "Tibati", "Bogo", "Yagoua", "Mbouda", "Bandjoun", "Bafang", "Fundong",
    "Wum", "Bali", "Batouri", "Abong-Mbang", "Akonolinga", "Obala",
    "Nanga-Eboko", "Monatele", "Ntui", "Eseka", "Loum", "Manjo", "Melong",
    "Penja", "Tiko", "Muyuka", "Mamfe", "Ndop", "Nkambe", "Kaele",
    "Mindif", "Gazawa", "Guiguidis", "Founangue",
]

CATEGORIES_CONCERNEES = ["geo_tabulaire", "scenario"]


def normaliser(texte):
    return supprimer_accents(str(texte).lower())


def trouver_villes_mentionnees(texte_normalise):
    """Retourne la liste des villes candidates trouvees dans le texte,
    avec correspondance sur mot entier (evite les faux positifs de
    sous-chaine)."""
    trouvees = []
    for ville in VILLES_CANDIDATES:
        motif = r"\b" + re.escape(normaliser(ville)) + r"\b"
        if re.search(motif, texte_normalise):
            trouvees.append(ville)
    return trouvees


def charger_donnees():
    df_s2 = pd.read_csv(FICHIER_S2, encoding="utf-8")
    df_s3 = pd.read_csv(FICHIER_S3, encoding="utf-8")
    colonnes = ["id", "categorie", "question", "reponse"]
    df = pd.concat([df_s2[colonnes], df_s3[colonnes]], ignore_index=True)
    return df


def main():
    print("Chargement des donnees S2 + S3...")
    df = charger_donnees()

    df_geo = df[df["categorie"].isin(CATEGORIES_CONCERNEES)].copy()
    print(f"{len(df_geo)} questions de categorie {CATEGORIES_CONCERNEES} a analyser\n")

    resultats = []
    for _, ligne in df_geo.iterrows():
        question_normalisee = normaliser(ligne["question"])
        reponse_normalisee = normaliser(ligne["reponse"])

        villes_dans_question = trouver_villes_mentionnees(question_normalisee)
        villes_dans_reponse = trouver_villes_mentionnees(reponse_normalisee)

        ville_demandee = villes_dans_question[0] if villes_dans_question else None
        villes_erronees = [v for v in villes_dans_reponse if v != ville_demandee]

        resultats.append({
            "id": ligne["id"],
            "categorie": ligne["categorie"],
            "question": ligne["question"],
            "ville_demandee": ville_demandee,
            "villes_erronees_detectees": ", ".join(villes_erronees) if villes_erronees else "",
            "confusion_detectee": len(villes_erronees) > 0,
            "reponse_extrait": str(ligne["reponse"])[:300],
        })

    df_resultats = pd.DataFrame(resultats)
    df_resultats.to_csv(FICHIER_RAPPORT, index=False, encoding="utf-8-sig")

    nb_confusions = df_resultats["confusion_detectee"].sum()
    taux = 100 * nb_confusions / len(df_resultats) if len(df_resultats) else 0

    print("=" * 60)
    print("RESULTAT")
    print("=" * 60)
    print(f"Questions analysees : {len(df_resultats)}")
    print(f"Confusions de ville detectees : {nb_confusions} ({taux:.1f}%)")
    print(f"\nDetail par categorie :")
    print(df_resultats.groupby("categorie")["confusion_detectee"].agg(["sum", "count", "mean"]))

    print(f"\nRapport complet sauvegarde dans : {FICHIER_RAPPORT}")

    if nb_confusions > 0:
        print("\nExemples de confusions detectees :")
        exemples = df_resultats[df_resultats["confusion_detectee"]].head(5)
        for _, ex in exemples.iterrows():
            print(f"\n  [{ex['id']}] Demande : {ex['ville_demandee']} "
                  f"| Villes erronees citees : {ex['villes_erronees_detectees']}")
            print(f"  Question : {ex['question']}")


if __name__ == "__main__":
    main()
