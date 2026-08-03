"""
Script d'ingestion du corpus — chunking et indexation vectorielle.

Ce script :
1. Charge tous les documents présents dans data/raw/ (.txt et .pdf)
2. NETTOIE le texte : retire les lignes de type footer/contact (URLs,
   emails, "CONTACTEZ-NOUS"...) et force une frontière de chunk avant
   chaque en-tête de région ("REGION DE ...", "REGION DU ...")
3. Découpe chaque document en chunks (morceaux de texte)
4. Génère les embeddings de chaque chunk (sentence-transformers)
5. Indexe le tout dans une base vectorielle FAISS, sauvegardée sur disque

Corrections apportees suite a un bug reel decouvert lors des tests :
une question sur les microfinances de Douala citait a tort un
etablissement de Garoua (CECICS), car le decoupage generique du texte
avait cree un chunk a cheval sur la fin de la section "REGION DU
LITTORAL" et le debut de "REGION DU NORD". Un autre chunk contenait par
ailleurs un encart publicitaire hors-sujet (site web, email de contact)
mentionnant incidemment "Douala".

Usage :
    python src/build_index.py

Prérequis :
    pip install langchain langchain-community faiss-cpu sentence-transformers pypdf
"""

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

# Motif des en-tetes de region dans le tableau EMF (ex. "REGION DU
# LITTORAL", "REGION DE L'EXTREME-NORD"). On force un saut de paragraphe
# ("\n\n") juste avant chaque occurrence, pour que le splitter (qui essaie
# "\n\n" en priorite) coupe preferentiellement a cette frontiere plutot
# que de melanger deux regions dans un meme chunk.
MOTIF_ENTETE_REGION = re.compile(r"(REGION D[EU] [A-ZÀÂÉÈÊÎÔÛÇ' \-]+)")

# Lignes typiques d'un footer/encart publicitaire hors-sujet (site web,
# email de contact, telephone), a retirer avant le chunking pour eviter
# qu'un chunk entier ne soit pollue par du contenu non pertinent.
MOTIFS_LIGNES_A_EXCLURE = [
    re.compile(r"www\.", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # adresse email
    re.compile(r"CONT\s*ACTEZ[\s-]*NOUS", re.IGNORECASE),
    re.compile(r"^\+?\d[\d\s]{7,}$"),  # ligne composee uniquement d'un numero de telephone
]


def nettoyer_texte(texte: str) -> str:
    """Retire les lignes de type footer/contact et force une frontiere
    de chunk avant chaque en-tete de region."""
    lignes_conservees = []
    for ligne in texte.splitlines():
        if any(motif.search(ligne) for motif in MOTIFS_LIGNES_A_EXCLURE):
            continue
        lignes_conservees.append(ligne)
    texte_nettoye = "\n".join(lignes_conservees)

    texte_nettoye = MOTIF_ENTETE_REGION.sub(r"\n\n\1", texte_nettoye)

    return texte_nettoye


def load_documents():
    """Charge tous les fichiers .txt et .pdf présents dans data/raw/,
    puis nettoie leur contenu (footers + frontieres de region)."""
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