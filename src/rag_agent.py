"""
Agent RAG maison — Microfinance au Cameroun.

Charge l'index FAISS déjà construit (voir build_index.py), se connecte
au LLM local (Llama 3.2 3B via Ollama), et répond aux questions en se
basant uniquement sur le contexte récupéré dans le corpus.

Chaque interaction est journalisée dans data/processed/interactions_log.csv.

Usage (mode interactif) :
    python src/rag_agent.py

Prérequis :
    - Ollama installé et lancé, avec le modèle llama3.2:3b téléchargé
    - Index FAISS déjà construit (python src/build_index.py)
    - pip install rank_bm25 (pour la recherche par mot-clé)
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
TOP_K = 5
# BM25_K : nombre de chunks retenus par la recherche par mot-cle, VOLONTAIREMENT
# plus large que TOP_K. Raison : EnsembleRetriever fusionne les CLASSEMENTS
# (Reciprocal Rank Fusion), pas les scores bruts. Un chunk pertinent doit donc
# apparaitre dans le top-k de BM25 pour la question complete (pas seulement
# pour un mot isole) afin d'etre pris en compte dans la fusion. Un pool plus
# large augmente les chances qu'un chunk rare (ex. nom de ville dans un
# tableau) y figure, meme si la question contient d'autres mots frequents
# qui accumulent aussi du score.
BM25_K = 20

# MAX_CONTEXTE_CHUNKS : nombre de chunks reellement envoyes au LLM apres
# fusion BM25+FAISS. On garde un pool de RECHERCHE large (BM25_K=20) pour
# maximiser les chances de capter le bon chunk meme mal classe, mais on ne
# transmet au LLM que les N meilleurs resultats APRES fusion (deja tries
# par pertinence par EnsembleRetriever). Sans cette limite, on envoyait
# jusqu'a 20-25 chunks au LLM, ce qui ralentissait fortement chaque
# reponse (192s en moyenne, jusqu'a 387s) sans forcement ameliorer la
# qualite : les chunks les moins bien classes apportent peu et allongent
# le temps de traitement.
MAX_CONTEXTE_CHUNKS = 12

# Mots vides francais retires avant le calcul du score BM25. Sans ce filtre,
# des mots tres frequents dans le corpus (quelles, sont, les, a...)
# noient le signal des mots rares et discriminants (ex. noms de villes).
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
    """Retire les accents (é -> e, à -> a, etc.) d'une chaîne.

    Nécessaire car BM25 compare des chaînes exactes : sans cette étape,
    une question tapée sans accent ("Yaounde") ne "matchait" pas un
    document contenant le mot avec accent ("Yaoundé"), ce qui faisait
    chuter le rang du bon chunk de la 9ème place (cas sans accent, ex.
    Maroua) à la 265ème place (cas avec accent, ex. Yaoundé).
    """
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


PROMPT_TEMPLATE = """Tu es un assistant qui répond aux questions sur la microfinance au Cameroun.

RÈGLES STRICTES :
1. Réponds UNIQUEMENT à partir des informations présentes dans le contexte ci-dessous.
2. N'utilise JAMAIS tes connaissances générales, même si tu penses connaître la réponse.
3. Si le contexte ne contient pas l'information demandée, réponds exactement :
   "Je ne dispose pas de cette information dans mes documents."
4. Ne cite aucun nom d'organisation, de lieu ou de chiffre qui n'apparaît pas explicitement dans le contexte.
5. Réponds en français, de manière concise et directe.

Contexte :
{context}

Question : {question}

Réponse :"""


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
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    bm25_retriever = BM25Retriever.from_documents(
        tous_les_documents,
        preprocess_func=pretraitement_bm25,
    )
    bm25_retriever.k = BM25_K

    return EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.5, 0.5],
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
    """Crée le fichier de log s'il n'existe pas, ou MIGRE automatiquement
    son en-tête s'il existe deja avec un ancien schema (moins de colonnes).

    Bug reel corrige ici : ce fichier a ete cree avant l'ajout de la
    colonne score_similarite au pipeline. Comme cette fonction n'ecrivait
    l'en-tete QUE si le fichier n'existait pas encore, les nouvelles
    lignes (8 champs) se sont ajoutees sous un en-tete qui n'en declarait
    que 7, desalignant tout le fichier. Desormais, si un en-tete existant
    est plus court que le schema attendu, TOUTES les lignes existantes
    sont migrees automatiquement (insertion d'une valeur vide pour la
    colonne manquante) avant que la moindre nouvelle ligne ne soit
    ajoutee — ce probleme ne peut plus se reproduire silencieusement.
    """
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
    """Calcule un score de similarité sémantique entre 0 et 1 (1 = très similaire).

    Le cahier des charges demande un "score de similarité" par interaction,
    valide entre 0 et 1 (section 4). FAISS retourne par defaut une DISTANCE
    L2 (0 = identique, plus grand = plus different, sans borne superieure
    fixe) et non une similarite normalisee. On applique donc la
    transformation 1 / (1 + distance) sur le meilleur resultat, qui donne
    une valeur toujours dans (0, 1], strictement decroissante avec la
    distance : proche de 1 si le document est tres proche semantiquement
    de la question, proche de 0 sinon.
    """
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
        # On ne garde que les N meilleurs resultats APRES fusion BM25+FAISS
        # (EnsembleRetriever les retourne deja tries par pertinence), pour
        # limiter le temps de traitement du LLM sans perdre le benefice du
        # pool de recherche large.
        docs = docs[:MAX_CONTEXTE_CHUNKS]
        contexte = "\n\n".join(doc.page_content for doc in docs)
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

    # L'ecriture du journal est protegee separement : un probleme
    # d'ecriture (fichier verrouille par un autre programme, permissions,
    # synchronisation OneDrive en cours...) ne doit jamais faire perdre
    # une reponse deja calculee par le LLM, potentiellement couteuse en
    # temps. On avertit sans interrompre le programme.
    try:
        log_interaction(question, reponse, len(docs), score_similarite, contexte, temps_reponse, statut)
    except Exception as e:
        print(f"/!\\ Echec de l'ecriture dans le journal (reponse conservee malgre tout) : {e}")

    return {
        "question": question,
        "reponse": reponse,
        "nb_documents": len(docs),
        "score_similarite": score_similarite,
        "temps_reponse": temps_reponse,
        "statut": statut,
    }


def main():
    print("Chargement de l'index vectoriel...")
    retriever, vectorstore = load_retriever()

    print(f"Connexion au LLM local ({LLM_MODEL} via Ollama)...")
    # IMPORTANT : par défaut, Ollama limite la fenêtre de contexte à 2048
    # tokens, quel que soit le modèle utilisé — même si Llama 3.2 3B peut
    # gérer beaucoup plus. Avec BM25_K=20 + FAISS TOP_K=5, on récupère
    # souvent 20-25 chunks (~800 caractères chacun), ce qui dépasse
    # largement 2048 tokens. Sans cet ajustement, Ollama tronque le
    # contexte SANS AUCUN AVERTISSEMENT : si les chunks pertinents tombent
    # dans la partie coupée, le modèle ne les voit jamais, même si le
    # retriever les avait bien récupérés.
    llm = Ollama(model=LLM_MODEL, num_ctx=8192)

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