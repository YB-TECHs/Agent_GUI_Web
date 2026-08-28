"""
Module build_index.py.
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"

import re
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

# Force un double saut de ligne avant les régions pour optimiser le chunking
MOTIF_ENTETE_REGION = re.compile(r"(REGION D[EU] [A-ZÀÂÉÈÊÎÔÛÇ' \-]+)")

# Nettoyage des footers et contacts pour éviter la pollution du RAG
MOTIFS_LIGNES_A_EXCLURE = [
    re.compile(r"www\.", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # email
    re.compile(r"CONT\s*ACTEZ[\s-]*NOUS", re.IGNORECASE),
    re.compile(r"^\+?\d[\d\s]{7,}$"),  # tel seul
]

def nettoyer_texte(texte: str) -> str:
    """Clean les footers et prépare le chunking par région."""
    lignes_conservees = []
    for ligne in texte.splitlines():
        if any(motif.search(ligne) for motif in MOTIFS_LIGNES_A_EXCLURE):
            continue
        lignes_conservees.append(ligne)
    texte_nettoye = "\n".join(lignes_conservees)
    texte_nettoye = MOTIF_ENTETE_REGION.sub(r"\n\n\1", texte_nettoye)
    return texte_nettoye

def load_documents():
    """Load et clean tous les pdf/txt."""
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
        try:
            loader = PyPDFLoader(str(f))
            documents.extend(loader.load())
        except Exception as e:
            print(f"    ÉCHEC : {f.name} ignoré (fichier corrompu ou illisible) -> {e}")

    for doc in documents:
        doc.page_content = nettoyer_texte(doc.page_content)

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


def main():
    documents = load_documents()
    print(f"\nTotal documents chargés : {len(documents)}")

    chunks = chunk_documents(documents)
    print(f"Total chunks générés : {len(chunks)}")

    build_and_save_index(chunks)

    print("\n--- Ingestion terminée ---")


if __name__ == "__main__":
    main()