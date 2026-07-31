"""
Script d'ingestion du corpus — chunking et indexation vectorielle.

Ce script :
1. Charge tous les documents présents dans data/raw/ (.txt et .pdf)
2. Découpe chaque document en chunks (morceaux de texte)
3. Génère les embeddings de chaque chunk (sentence-transformers)
4. Indexe le tout dans une base vectorielle FAISS, sauvegardée sur disque

Usage :
    python src/build_index.py

Prérequis :
    pip install langchain langchain-community faiss-cpu sentence-transformers pypdf
"""

import pickle
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

RAW_DIR = Path("data/raw")
INDEX_DIR = Path("data/processed/faiss_index")

# Modèle d'embedding multilingue, léger, adapté au CPU et au français
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Paramètres de chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def load_documents():
    """Charge tous les fichiers .txt et .pdf présents dans data/raw/."""
    documents = []

    txt_files = sorted(RAW_DIR.glob("*.txt"))
    pdf_files = sorted(RAW_DIR.glob("*.pdf"))

    print(f"Fichiers texte trouvés : {len(txt_files)}")
    print(f"Fichiers PDF trouvés : {len(pdf_files)}")

    for f in txt_files:
        print(f"  Chargement : {f.name}")
        loader = TextLoader(str(f), encoding="utf-8")
        documents.extend(loader.load())

    for f in pdf_files:
        print(f"  Chargement : {f.name}")
        loader = PyPDFLoader(str(f))
        documents.extend(loader.load())

    return documents


def chunk_documents(documents):
    """Découpe les documents en chunks de taille contrôlée."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    return chunks


def build_and_save_index(chunks):
    """Génère les embeddings et construit l'index FAISS, puis le sauvegarde."""
    print(f"\nChargement du modèle d'embedding ({EMBEDDING_MODEL})...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"Indexation de {len(chunks)} chunks (cela peut prendre quelques minutes sur CPU)...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"Index FAISS sauvegardé dans : {INDEX_DIR}")

    # Sauvegarde des chunks bruts (nécessaire pour la recherche par mot-clé BM25)
    chunks_path = INDEX_DIR.parent / "chunks.pkl"
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)
    print(f"Chunks bruts sauvegardés dans : {chunks_path}")


def main():
    documents = load_documents()
    print(f"\nTotal documents chargés : {len(documents)}")

    chunks = chunk_documents(documents)
    print(f"Total chunks générés : {len(chunks)}")

    build_and_save_index(chunks)

    print("\n--- Ingestion terminée ---")


if __name__ == "__main__":
    main()
