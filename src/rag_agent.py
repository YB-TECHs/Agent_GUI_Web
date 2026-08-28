"""
Module rag_agent.py.
"""

import csv
import importlib
import importlib.util
import os
import time
import unicodedata
from datetime import datetime
from pathlib import Path

# Evite les erreurs reseau HuggingFace si une verification en ligne
# est tentee alors que le modele est deja en cache local.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain_community.retrievers import BM25Retriever


def load_ensemble_retriever_class():
    for module_name in ("langchain.retrievers", "langchain_classic.retrievers"):
        if importlib.util.find_spec(module_name) is not None:
            module = importlib.import_module(module_name)
            return module.EnsembleRetriever
    raise ImportError(
        "Aucun module EnsembleRetriever trouvé : installez langchain ou langchain_classic."
    )

EnsembleRetriever = load_ensemble_retriever_class()

INDEX_DIR = Path("data/processed/faiss_index")
LOG_FILE = Path("data/processed/interactions_log.csv")

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama3.2:3b"

# TOP_K final : nombre de chunks FAISS (semantiques) retenus.
TOP_K = 15
# BM25_K : nombre de chunks retenus par la recherche par mot-cle
BM25_K = 40

# Limite du contexte envoyé au LLM pour éviter la surcharge (Lost in the middle)
MAX_CONTEXTE_CHUNKS = 8

# Stopwords FR pour optimiser BM25
MOTS_VIDES_FRANCAIS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
    "et", "ou", "est", "sont", "es", "suis", "sommes", "etes",
    "a", "à", "au", "aux", "en", "dans", "sur", "par", "pour",
    "avec", "sans", "ce", "cet", "cette", "ces", "que", "qu",
    "qui", "quoi", "quel", "quelle", "quels", "quelles",
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "se", "s", "son", "sa", "ses", "leur", "leurs", "y", "ne", "pas",
}


def supprimer_accents(texte: str) -> str:
    """Normalisation des accents pour BM25."""
    forme_decomposee = unicodedata.normalize("NFD", texte)
    return "".join(c for c in forme_decomposee if unicodedata.category(c) != "Mn")


def pretraitement_bm25(texte: str) -> list[str]:
    """Tokenisation utilisee par BM25 : minuscule + sans accents + retrait des mots vides.

    Exposee au niveau du module (plutot qu'imbriquee dans load_retriever)
    pour pouvoir etre reutilisee telle quelle dans les scripts de
    diagnostic, et garantir qu'on teste toujours exactement la meme
    logique que celle utilisee en production.
    """
    texte_normalise = supprimer_accents(texte.lower())
    tokens = texte_normalise.split()
    return [t for t in tokens if t not in MOTS_VIDES_FRANCAIS]


PROMPT_TEMPLATE = """Tu es un expert en microfinance.
Analyse la question et réponds en te basant STRICTEMENT sur le CONTEXTE fourni.

CONSIGNE : 
Si la question aborde plusieurs sujets, sépare ta réponse en deux.
1. Réponds aux sujets présents dans le contexte.
2. Pour les sujets hors-contexte, écris explicitement : "Cependant, je ne dispose pas d'informations sur ce sujet."
N'invente JAMAIS d'informations.

CONTEXTE :
{context}

Question : {question}
Réponse :"""

def formater_contexte(docs):
    """Formate les chunks en les numerotant pour aider le LLM a les distinguer."""
    return "\n\n".join([f"--- Extrait {i+1} ---\n{doc.page_content}" for i, doc in enumerate(docs)])

def charger_tous_les_chunks():
    """Charge l'index FAISS et retourne (vectorstore, liste de tous les chunks)."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
    )
    tous_les_documents = list(vectorstore.docstore._dict.values())
    return vectorstore, tous_les_documents


def load_retriever():
    """Charge l'index FAISS et retourne un retriever hybride mot-clé + sémantique.

    Problème résolu : la recherche par similarité sémantique seule ne
    retrouvait pas certains chunks issus de données tabulaires (ex. listes
    d'établissements de microfinance par ville), car leur texte extrait
    perd sa cohérence grammaticale lors de l'extraction du PDF. On combine
    donc FAISS (recherche sémantique) avec BM25 (recherche par mot-clé
    exact), qui retrouve directement un chunk contenant un nom de ville
    ou d'institution même si sa structure nuit à l'embedding sémantique.
    """
    vectorstore, tous_les_documents = charger_tous_les_chunks()
    
    faiss_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": TOP_K, "fetch_k": 50, "lambda_mult": 0.5}
    )

    bm25_retriever = BM25Retriever.from_documents(
        tous_les_documents,
        preprocess_func=pretraitement_bm25,
    )
    bm25_retriever.k = BM25_K

    return EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.6, 0.4]
    ), vectorstore


COLONNES_LOG_ATTENDUES = [
    "timestamp",
    "question",
    "reponse",
    "nb_documents_recuperes",
    "score_similarite",
    "extrait_contexte",
    "temps_reponse_secondes",
    "statut",
]


def init_log_file():
    """Crée le fichier de log s'il n'existe pas, ou met à jour le schéma si nécessaire."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLONNES_LOG_ATTENDUES)
        return

    with open(LOG_FILE, newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        entete_actuel = next(lecteur, [])
        if entete_actuel == COLONNES_LOG_ATTENDUES:
            return  # deja a jour, rien a faire

        print(f"/!\\ En-tete du journal obsolete detecte ({len(entete_actuel)} colonnes "
              f"au lieu de {len(COLONNES_LOG_ATTENDUES)}). Migration automatique en cours...")
        toutes_les_lignes = list(lecteur)

    colonnes_manquantes = len(COLONNES_LOG_ATTENDUES) - len(entete_actuel)
    lignes_migrees = []
    for ligne in toutes_les_lignes:
        if len(ligne) == len(entete_actuel) and colonnes_manquantes > 0:
            # Insere les colonnes manquantes juste avant "extrait_contexte"
            # (position 4 dans le schema actuel), sans rien inventer.
            ligne_migree = ligne[:4] + [""] * colonnes_manquantes + ligne[4:]
            lignes_migrees.append(ligne_migree)
        else:
            lignes_migrees.append(ligne)  # deja au bon format ou anomalie a part

    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(COLONNES_LOG_ATTENDUES)
        ecrivain.writerows(lignes_migrees)

    print(f"Migration terminee : {len(lignes_migrees)} ligne(s) mise(s) a jour "
          f"vers le nouveau schema.")


def log_interaction(question, reponse, nb_docs, score_similarite, extrait_contexte, temps_reponse, statut):
    """Ajoute une ligne au journal des interactions."""
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                question,
                reponse,
                nb_docs,
                round(score_similarite, 4) if score_similarite is not None else "",
                extrait_contexte[:200],  # aperçu limité pour la lisibilité du CSV
                round(temps_reponse, 2),
                statut,
            ]
        )


def calculer_score_similarite(question: str, vectorstore) -> float:
    """Convertit la distance L2 de FAISS en score de similarité entre 0 et 1."""
    resultats = vectorstore.similarity_search_with_score(question, k=1)
    if not resultats:
        return 0.0
    _, distance = resultats[0]
    return 1 / (1 + distance)


def ask(question: str, retriever, llm, vectorstore) -> dict:
    """Pose une question à l'agent RAG et retourne la réponse + métadonnées."""
    start = time.time()
    statut = "succes"

    try:
        docs = retriever.invoke(question)
        # On limite le contexte pour ne pas surcharger le modèle local
        docs = docs[:MAX_CONTEXTE_CHUNKS]
        contexte = formater_contexte(docs)
        prompt = PROMPT_TEMPLATE.format(context=contexte, question=question)
        reponse = llm.invoke(prompt)
        score_similarite = calculer_score_similarite(question, vectorstore)
    except Exception as e:
        docs = []
        contexte = ""
        reponse = f"Erreur lors du traitement de la requête : {e}"
        statut = "echec"
        score_similarite = None

    temps_reponse = time.time() - start

    # Sauvegarde asynchrone pour ne pas crasher si le fichier est ouvert ailleurs
    try:
        log_interaction(question, reponse, len(docs), score_similarite, contexte, temps_reponse, statut)
    except Exception as e:
        print(f"/!\\ Echec de l'ecriture CSV : {e}")

    return {
        "question": question,
        "reponse": reponse,
        "nb_documents": len(docs),
        "sources": list(set([doc.metadata.get("source") for doc in docs if doc.metadata.get("source")])),
        "score_similarite": score_similarite,
        "temps_reponse": temps_reponse,
        "statut": statut,
    }


def main():
    print("Chargement de l'index vectoriel...")
    retriever, vectorstore = load_retriever()

    print(f"Connexion au LLM local ({LLM_MODEL} via Ollama)...")
    # Augmentation du contexte (4096) pour éviter la troncature silencieuse d'Ollama
    llm = Ollama(model=LLM_MODEL, num_ctx=4096, temperature=0.0)

    init_log_file()

    print("\nAgent RAG prêt. Tape ta question, ou 'exit' pour quitter.\n")

    while True:
        question = input("Question > ").strip()
        if question.lower() in ("exit", "quit", ""):
            print("Fin de session.")
            break

        result = ask(question, retriever, llm, vectorstore)

        print(f"\nRéponse ({result['temps_reponse']:.1f}s, "
              f"{result['nb_documents']} document(s) récupéré(s), "
              f"score de similarité : {result['score_similarite']:.3f}) :")
        print(result["reponse"])
        print()


if __name__ == "__main__":
    main()