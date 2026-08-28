"""
Module diagnostic_rang_bm25.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from langchain_community.retrievers import BM25Retriever

from rag_agent import charger_tous_les_chunks, pretraitement_bm25

QUESTION = "quelles sont les microfinances presentes a maroua ?"


def main():
    print("Chargement des chunks...")
    _, tous_les_documents = charger_tous_les_chunks()
    print(f"Nombre total de chunks : {len(tous_les_documents)}")

    print("Tokens retenus pour la question (apres retrait des mots vides) :")
    print(pretraitement_bm25(QUESTION))

    bm25 = BM25Retriever.from_documents(
        tous_les_documents,
        preprocess_func=pretraitement_bm25,
    )
    # On demande le classement complet pour voir où se situe le bon chunk.
    bm25.k = len(tous_les_documents)

    classement_complet = bm25.invoke(QUESTION)

    print(f"\n{'='*60}")
    print("Position des chunks contenant 'Maroua' dans le classement BM25")
    print("=" * 60)
    trouve = False
    for rang, doc in enumerate(classement_complet, start=1):
        if "Maroua" in doc.page_content:
            trouve = True
            print(f"Rang {rang} / {len(classement_complet)} :")
            print(doc.page_content[:200])
            print()

    if not trouve:
        print("Aucun chunk contenant 'Maroua' n'a ete retourne par BM25 "
              "pour cette question, meme dans le classement complet.")

    print("=" * 60)
    print("Top 10 du classement BM25 (pour comparaison) :")
    print("=" * 60)
    for rang, doc in enumerate(classement_complet[:10], start=1):
        contient_maroua = "Maroua" in doc.page_content
        print(f"Rang {rang} (contient Maroua : {contient_maroua}) : "
              f"{doc.page_content[:100]!r}")


if __name__ == "__main__":
    main()
