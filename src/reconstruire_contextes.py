"""
Module reconstruire_contextes.py.
"""

import csv
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

import pandas as pd

from rag_agent import load_retriever

FICHIER_DATASET = Path("data/processed/dataset_final_nettoye.csv")
FICHIER_SORTIE = Path("data/processed/contextes_pour_ragas.csv")


def main():
    print("Chargement du dataset final...")
    df = pd.read_csv(FICHIER_DATASET, encoding="utf-8")
    print(f"{len(df)} interactions a traiter")

    print("Chargement du retriever (index FAISS + BM25)...")
    retriever, _vectorstore = load_retriever()

    with open(FICHIER_SORTIE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question", "reponse", "categorie", "contexte_complet"])

        for i, ligne in df.iterrows():
            docs = retriever.invoke(ligne["question"])
            docs = docs[:12]  # meme limite que MAX_CONTEXTE_CHUNKS en production
            contexte = "\n\n".join(doc.page_content for doc in docs)

            writer.writerow([ligne["id"], ligne["question"], ligne["reponse"], ligne["categorie"], contexte])

            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(df)} contextes reconstruits...")

    print(f"\nTermine. Contextes sauvegardes dans : {FICHIER_SORTIE}")
    print("Aucun appel au LLM n'a ete necessaire pour cette etape (rapide).")


if __name__ == "__main__":
    main()
