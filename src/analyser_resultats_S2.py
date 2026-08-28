"""
Module analyser_resultats_S2.py.
"""

from pathlib import Path

import pandas as pd

RESULTS_FILE = Path("data/processed/resultats_tests_S2.csv")
PHRASE_ABSTENTION = "Je ne dispose pas de cette information"


def main():
    df = pd.read_csv(RESULTS_FILE)

    print("=" * 60)
    print("RESUME GLOBAL")
    print("=" * 60)
    print(f"Nombre total de questions testees : {len(df)}")
    print(f"Temps de reponse moyen : {df['temps_reponse_secondes'].mean():.1f}s")
    print(f"Temps de reponse median : {df['temps_reponse_secondes'].median():.1f}s")
    print(f"Temps de reponse max : {df['temps_reponse_secondes'].max():.1f}s")
    print(f"Echecs techniques (erreurs) : {(df['statut'] == 'echec').sum()}")

    df["abstention"] = df["reponse"].str.contains(PHRASE_ABSTENTION, case=False, na=False)
    print(f"Reponses en abstention (\"je ne sais pas\") : "
          f"{df['abstention'].sum()} / {len(df)} "
          f"({100 * df['abstention'].mean():.1f}%)")

    print("\n" + "=" * 60)
    print("PAR CATEGORIE")
    print("=" * 60)
    resume_categorie = df.groupby("categorie").agg(
        nb_questions=("id", "count"),
        temps_moyen_s=("temps_reponse_secondes", "mean"),
        nb_abstentions=("abstention", "sum"),
    ).round(1)
    print(resume_categorie)

    # Verification cible : les questions geo_tabulaire sont celles ou
    # on a identifie une limite connue du retrieval semantique.
    print("\n" + "=" * 60)
    print("FOCUS : questions geo_tabulaire (limite retrieval connue)")
    print("=" * 60)
    geo = df[df["categorie"] == "geo_tabulaire"][["question", "abstention", "temps_reponse_secondes"]]
    print(geo.to_string(index=False))

    # Sauvegarde d'un resume exploitable pour le rapport
    resume_categorie.to_csv("data/processed/resume_par_categorie_S2.csv")
    print("\nResume par categorie sauvegarde dans : data/processed/resume_par_categorie_S2.csv")


if __name__ == "__main__":
    main()
