"""
Script de diagnostic (generalise) — verifie ce que le retriever hybride
complet (BM25 + FAISS, apres fusion) renvoie pour une question donnee,
sans passer par le LLM. Version generalisee de diagnostic_retriever.py,
utilisable pour n'importe quelle ville/mot sans modifier le code.

Usage :
    python src/diagnostic_retriever_generique.py "question ici" mot_a_chercher
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rag_agent import load_retriever


def main():
    if len(sys.argv) != 3:
        print('Usage : python src/diagnostic_retriever_generique.py "la question" mot_a_chercher')
        sys.exit(1)

    question = sys.argv[1]
    mot = sys.argv[2]

    print("Chargement du retriever hybride...")
    retriever, _vectorstore = load_retriever()

    print(f"\nQuestion testee : {question}\n")
    docs = retriever.invoke(question)

    print(f"Nombre de documents recuperes : {len(docs)}")
    nb_avec_mot = sum(1 for d in docs if mot in d.page_content)
    print(f"Nombre de documents contenant '{mot}' : {nb_avec_mot}\n")

    for i, doc in enumerate(docs):
        contient_mot = mot in doc.page_content
        marqueur = " <-- CONTIENT LE MOT" if contient_mot else ""
        print(f"--- Doc {i+1} (contient '{mot}' : {contient_mot}){marqueur} ---")
        print(doc.page_content[:150])
        print()


if __name__ == "__main__":
    main()