"""
Module corriger_reponses_confuses.py.
"""

import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import pandas as pd
from langchain_community.llms import Ollama

from rag_agent import LLM_MODEL, ask, init_log_file, load_retriever

FICHIER_RAPPORT_CONFUSION = Path("data/processed/rapport_confusion_villes.csv")
FICHIER_S2 = Path("data/processed/resultats_tests_S2.csv")
FICHIER_S3 = Path("data/processed/dataset_interactions_S3.csv")
FICHIER_CORRECTIONS = Path("data/processed/corrections_confusion_villes.csv")


def charger_ids_a_corriger():
    df_rapport = pd.read_csv(FICHIER_RAPPORT_CONFUSION, encoding="utf-8")
    df_confuses = df_rapport[df_rapport["confusion_detectee"] == True]
    return df_confuses[["id", "categorie", "question"]].to_dict("records")


def recuperer_anciennes_valeurs(id_a_chercher):
    """Retrouve les anciennes valeurs (avant correction) depuis S2 ou S3,
    pour tracer precisement ce qui a change."""
    for fichier in (FICHIER_S2, FICHIER_S3):
        df = pd.read_csv(fichier, encoding="utf-8")
        ligne = df[df["id"] == id_a_chercher]
        if not ligne.empty:
            return ligne.iloc[0].to_dict()
    return None


def main():
    a_corriger = charger_ids_a_corriger()
    print(f"{len(a_corriger)} question(s) a regenerer avec l'index corrige :\n")
    for item in a_corriger:
        print(f"  [{item['id']}] {item['question']}")

    print("\nChargement de l'index vectoriel CORRIGE...")
    retriever, vectorstore = load_retriever()

    print(f"Connexion au LLM local ({LLM_MODEL} via Ollama)...")
    llm = Ollama(model=LLM_MODEL, num_ctx=8192)

    init_log_file()

    resultats_corrections = []

    for i, item in enumerate(a_corriger, start=1):
        print(f"\n[{i}/{len(a_corriger)}] Regeneration : {item['question']}")

        anciennes_valeurs = recuperer_anciennes_valeurs(item["id"])

        result = ask(item["question"], retriever, llm, vectorstore)
        score = result["score_similarite"]

        print(f"    -> {result['temps_reponse']:.1f}s, "
              f"{result['nb_documents']} document(s), statut={result['statut']}")

        resultats_corrections.append({
            "id": item["id"],
            "categorie": item["categorie"],
            "question": item["question"],
            "ancienne_reponse": anciennes_valeurs["reponse"] if anciennes_valeurs else "",
            "nouvelle_reponse": result["reponse"],
            "ancien_nb_documents": anciennes_valeurs["nb_documents_recuperes"] if anciennes_valeurs else None,
            "nouveau_nb_documents": result["nb_documents"],
            "nouveau_score_similarite": round(score, 4) if score is not None else "",
            "ancien_temps_reponse": anciennes_valeurs["temps_reponse_secondes"] if anciennes_valeurs else None,
            "nouveau_temps_reponse": round(result["temps_reponse"], 2),
            "ancien_statut": anciennes_valeurs["statut"] if anciennes_valeurs else "",
            "nouveau_statut": result["statut"],
        })

    df_corrections = pd.DataFrame(resultats_corrections)
    df_corrections.to_csv(FICHIER_CORRECTIONS, index=False, encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"Corrections sauvegardees dans : {FICHIER_CORRECTIONS}")
    print(f"{'='*60}")
    print("\nAucun fichier brut original n'a ete modifie. "
          "Lance maintenant nettoyage_dataset.py, qui appliquera ces "
          "corrections de facon tracee (colonne dediee) sur le dataset final.")


if __name__ == "__main__":
    main()
