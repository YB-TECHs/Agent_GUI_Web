"""
Module run_test_questions.py.
"""

import csv
import os
import time
from pathlib import Path

# Evite les erreurs reseau HuggingFace si une verification en ligne
# est tentee alors que le modele est deja en cache local.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from langchain_community.llms import Ollama

from rag_agent import LLM_MODEL, ask, init_log_file, load_retriever

QUESTIONS_FILE = Path("test_questions.csv")
RESULTS_FILE = Path("data/processed/resultats_tests_S2.csv")


def load_questions():
    """Charge la liste de questions depuis le CSV (id, categorie, question)."""
    with open(QUESTIONS_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def init_results_file():
    """Cree le fichier de resultats dedie a la tests S2."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "categorie",
                "question",
                "reponse",
                "nb_documents_recuperes",
                "score_similarite",
                "temps_reponse_secondes",
                "statut",
            ]
        )


def log_result(item, result):
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        score = result["score_similarite"]
        writer.writerow(
            [
                item["id"],
                item["categorie"],
                item["question"],
                result["reponse"],
                result["nb_documents"],
                round(score, 4) if score is not None else "",
                round(result["temps_reponse"], 2),
                result["statut"],
            ]
        )


def main():
    questions = load_questions()
    print(f"{len(questions)} questions chargees depuis {QUESTIONS_FILE}\n")

    print("Chargement de l'index vectoriel...")
    retriever, vectorstore = load_retriever()

    print(f"Connexion au LLM local ({LLM_MODEL} via Ollama)...")
    llm = Ollama(model=LLM_MODEL)

    init_log_file()
    init_results_file()

    debut_campagne = time.time()

    for i, item in enumerate(questions, start=1):
        print(f"[{i}/{len(questions)}] ({item['categorie']}) {item['question']}")

        result = ask(item["question"], retriever, llm, vectorstore)
        log_result(item, result)

        print(
            f"    -> {result['temps_reponse']:.1f}s, "
            f"{result['nb_documents']} document(s), statut={result['statut']}"
        )

        ecoule = time.time() - debut_campagne
        moyenne = ecoule / i
        restant = moyenne * (len(questions) - i)
        print(f"    -> temps restant estime : {restant/60:.1f} min\n")

    print(f"Campagne terminee. Resultats detailles dans : {RESULTS_FILE}")
    print(f"Journal complet des interactions dans : data/processed/interactions_log.csv")


if __name__ == "__main__":
    main()