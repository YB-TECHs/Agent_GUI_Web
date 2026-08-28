"""
Module diagnostic_bm25_seul.py.
"""

from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

INDEX_DIR = Path("data/processed/faiss_index")
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

QUESTIONS = [
    "quelles sont les microfinances presentes a maroua ?",
    "maroua",
    "Maroua",
]


def pretraitement_insensible_a_la_casse(texte: str):
    return texte.lower().split()


def main():
    print("Chargement de l'index FAISS (pour recuperer les chunks)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )
    tous_les_documents = list(vectorstore.docstore._dict.values())
    print(f"Nombre total de chunks charges : {len(tous_les_documents)}")

    print("Construction de BM25Retriever...")
    bm25 = BM25Retriever.from_documents(
        tous_les_documents,
        preprocess_func=pretraitement_insensible_a_la_casse,
    )
    bm25.k = 5

    for question in QUESTIONS:
        print(f"\n{'='*60}")
        print(f"Question BM25 : {question!r}")
        print("=" * 60)
        docs = bm25.invoke(question)
        for i, doc in enumerate(docs):
            contient_maroua = "Maroua" in doc.page_content
            print(f"--- Doc {i+1} (contient 'Maroua' : {contient_maroua}) ---")
            print(doc.page_content[:150])
            print()


if __name__ == "__main__":
    main()
