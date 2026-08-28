"""
Module diagnostic_rang_mot.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from langchain_community.retrievers import BM25Retriever

from rag_agent import BM25_K, charger_tous_les_chunks, pretraitement_bm25


def main():
    if len(sys.argv) != 3:
        print('Usage : python src/diagnostic_rang_mot.py "la question" mot_a_chercher')
        sys.exit(1)

    question = sys.argv[1]
    mot = sys.argv[2]

    print("Chargement des chunks...")
    _, tous_les_documents = charger_tous_les_chunks()
    print(f"Nombre total de chunks : {len(tous_les_documents)}")

    nb_chunks_avec_mot = sum(1 for d in tous_les_documents if mot in d.page_content)
    print(f"Nombre de chunks contenant '{mot}' : {nb_chunks_avec_mot}")

    print(f"\nTokens retenus pour la question (apres retrait des mots vides) :")
    print(pretraitement_bm25(question))

    bm25 = BM25Retriever.from_documents(
        tous_les_documents,
        preprocess_func=pretraitement_bm25,
    )
    bm25.k = len(tous_les_documents)

    classement_complet = bm25.invoke(question)

    print(f"\n{'='*60}")
    print(f"Rangs des chunks contenant '{mot}' (BM25_K de production = {BM25_K})")
    print("=" * 60)
    rangs_trouves = []
    for rang, doc in enumerate(classement_complet, start=1):
        if mot in doc.page_content:
            rangs_trouves.append(rang)

    if rangs_trouves:
        print(f"Rangs : {rangs_trouves}")
        nb_dans_pool = sum(1 for r in rangs_trouves if r <= BM25_K)
        print(f"\nNombre de ces chunks qui entreraient dans le pool BM25_K={BM25_K} : "
              f"{nb_dans_pool} / {len(rangs_trouves)}")
        meilleur_rang = min(rangs_trouves)
        if meilleur_rang > BM25_K:
            print(f"\n/!\\ Le meilleur rang ({meilleur_rang}) depasse BM25_K={BM25_K}.")
            print(f"    Il faudrait un BM25_K d'au moins {meilleur_rang} pour capter "
                  f"ce chunk.")
    else:
        print(f"Aucun chunk contenant '{mot}' n'apparait dans le classement BM25 "
              f"pour cette question (situation anormale si le mot existe dans le corpus).")


if __name__ == "__main__":
    main()
