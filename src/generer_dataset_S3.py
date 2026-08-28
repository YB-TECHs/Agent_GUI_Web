"""
Module generer_dataset_S3.py.
"""

import csv
import os
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

from langchain_community.llms import Ollama

from rag_agent import LLM_MODEL, ask, init_log_file, load_retriever
from empecher_veille import EmpecherVeille

QUESTIONS_FILE = Path("questions_dataset_S3.csv")
RESULTS_FILE = Path("data/processed/dataset_interactions_S3.csv")
ANCIEN_RESULTS_FILE = Path("data/processed/dataset_interactions_S3_avant_correction.csv")

COLONNES = [
    "id", "categorie", "question", "reponse", "nb_documents_recuperes",
    "score_similarite", "temps_reponse_secondes", "statut",
]


def charger_questions():
    with open(QUESTIONS_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def archiver_resultats_existants_si_besoin():
    """Renomme l'ancien fichier de resultats en archive, une seule fois,
    pour ne jamais perdre de travail deja effectue lors d'une session
    anterieure basee sur une liste de questions differente."""
    if RESULTS_FILE.exists() and not ANCIEN_RESULTS_FILE.exists():
        RESULTS_FILE.rename(ANCIEN_RESULTS_FILE)
        print(f"Ancien fichier de resultats archive dans : {ANCIEN_RESULTS_FILE}")


def charger_reponses_deja_calculees_par_texte():
    """Construit un dict {texte_question: ligne_resultat} a partir de
    TOUTES les sources disponibles (archive de l'ancienne session +
    fichier de resultats de la session en cours si deja partiellement
    rempli), pour retrouver le travail deja fait peu importe son origine."""
    reponses = {}
    for fichier in (ANCIEN_RESULTS_FILE, RESULTS_FILE):
        if fichier.exists():
            with open(fichier, newline="", encoding="utf-8") as f:
                for ligne in csv.DictReader(f):
                    reponses[ligne["question"]] = ligne
    return reponses


def init_results_file(colonnes=COLONNES):
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(colonnes)


def ecrire_ligne(item, reponse, nb_docs, score, temps_reponse, statut):
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                item["id"],
                item["categorie"],
                item["question"],
                reponse,
                nb_docs,
                score,
                temps_reponse,
                statut,
            ]
        )


def main():
    archiver_resultats_existants_si_besoin()
    reponses_connues = charger_reponses_deja_calculees_par_texte()
    print(f"{len(reponses_connues)} reponses deja disponibles (toutes sources confondues, "
          f"correspondance par texte de question)")

    toutes_les_questions = charger_questions()
    print(f"{len(toutes_les_questions)} questions au total dans {QUESTIONS_FILE}")

    init_results_file()

    # Questions deja presentes dans LE FICHIER DE SORTIE ACTUEL (evite les
    # doublons si le script est relance plusieurs fois de suite).
    deja_dans_sortie = set()
    with open(RESULTS_FILE, newline="", encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            deja_dans_sortie.add(ligne["question"])

    a_reutiliser = []
    a_calculer = []
    for q in toutes_les_questions:
        if q["question"] in deja_dans_sortie:
            continue  # deja ecrit dans le fichier de sortie actuel, on saute
        elif q["question"] in reponses_connues:
            a_reutiliser.append(q)
        else:
            a_calculer.append(q)

    print(f"{len(a_reutiliser)} questions reutilisees depuis une session precedente (sans recalcul)")
    print(f"{len(a_calculer)} questions vraiment nouvelles a calculer\n")

    # Etape 1 : recopier immediatement les reponses reutilisables (rapide,
    # pas besoin du LLM ni de l'index pour cette partie).
    for item in a_reutiliser:
        ancienne_ligne = reponses_connues[item["question"]]
        ecrire_ligne(
            item,
            ancienne_ligne["reponse"],
            ancienne_ligne["nb_documents_recuperes"],
            ancienne_ligne["score_similarite"],
            ancienne_ligne["temps_reponse_secondes"],
            ancienne_ligne["statut"],
        )
    if a_reutiliser:
        print(f"{len(a_reutiliser)} reponses recopiees depuis l'historique.\n")

    if not a_calculer:
        print("Rien de plus a calculer : toutes les questions sont couvertes "
              "(reutilisees ou deja dans le fichier de sortie).")
        return

    print("Chargement de l'index vectoriel...")
    retriever, vectorstore = load_retriever()

    print(f"Connexion au LLM local ({LLM_MODEL} via Ollama)...")
    llm = Ollama(model=LLM_MODEL, num_ctx=8192)

    init_log_file()

    debut_session = time.time()

    with EmpecherVeille():
        for i, item in enumerate(a_calculer, start=1):
            print(f"[{i}/{len(a_calculer)}] ({item['categorie']}) {item['question']}")

            result = ask(item["question"], retriever, llm, vectorstore)
            score = result["score_similarite"]
            ecrire_ligne(
                item,
                result["reponse"],
                result["nb_documents"],
                round(score, 4) if score is not None else "",
                round(result["temps_reponse"], 2),
                result["statut"],
            )

            score_txt = f"{score:.3f}" if score is not None else "N/A"
            print(f"    -> {result['temps_reponse']:.1f}s, "
                  f"{result['nb_documents']} document(s), "
                  f"score={score_txt}, statut={result['statut']}")

            ecoule = time.time() - debut_session
            moyenne = ecoule / i
            restant = moyenne * (len(a_calculer) - i)
            print(f"    -> temps restant estime (session actuelle) : {restant/60:.1f} min\n")

    print(f"Session terminee. Resultats cumules dans : {RESULTS_FILE}")
    print("Si le script a ete interrompu puis relance, relance-le simplement "
          "a nouveau : il reprendra automatiquement la ou il s'etait arrete.")


if __name__ == "__main__":
    main()