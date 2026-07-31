"""
Script de diagnostic — vérifie ce que le retriever hybride (BM25 + FAISS)
renvoie réellement pour une question donnée, sans passer par le LLM.

Usage :
    python src/diagnostic_retriever.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rag_agent import load_retriever

QUESTION = "quelles sont les microfinances presentes a maroua ?"


def main():
    print("Chargement du retriever hybride...")
    retriever, _vectorstore = load_retriever()

    print(f"\nQuestion testee : {QUESTION}\n")
    docs = retriever.invoke(QUESTION)

    print(f"Nombre de documents recuperes : {len(docs)}\n")
    for i, doc in enumerate(docs):
        contient_maroua = "Maroua" in doc.page_content
        print(f"--- Doc {i+1} (contient 'Maroua' : {contient_maroua}) ---")
        print(doc.page_content[:200])
        print()


if __name__ == "__main__":
    main()