"""
Module ragas_pilote.py.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import ragas_compat  # noqa: F401

import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas_llm_factory import creer_llm_ragas

from rag_agent import EMBEDDING_MODEL


FICHIER_CONTEXTES = Path("data/processed/contextes_pour_ragas.csv")
FICHIER_SORTIE = Path("data/processed/ragas_pilote_resultats.csv")
# QUOTA FREE TIER : 20 requetes/jour pour gemini-3.7-flash.
# 4 questions x 3 metriques = 12 requetes -- marge de securite de 8 requetes.
# Ajuster via : $env:RAGAS_TAILLE_PILOTE="N"
TAILLE_PILOTE = int(os.environ.get("RAGAS_TAILLE_PILOTE", "4"))
NOMBRE_CONTEXTES_EVALUES = 4
TAILLE_MAX_CONTEXTE_CARACTERES = 1800
DELAI_RAGAS_SECONDES = 300   # 5 minutes par requete
TRAVAILLEURS_RAGAS = 1        # 1 worker sequentiel : respecte le quota


def charger_metriques():
    """Charge les 3 metriques RAGAS standard.

    Avec Gemini comme juge, toutes les metriques fonctionnent :
    - Faithfulness : la reponse est-elle fidele au contexte ?
    - AnswerRelevancy : la reponse repond-elle bien a la question ?
    - LLMContextPrecisionWithoutReference : les chunks recuperes sont-ils
      pertinents par rapport a la question ?
    """
    try:
        from ragas.metrics import (
            Faithfulness,
            AnswerRelevancy,
            LLMContextPrecisionWithoutReference,
        )
        return [
            Faithfulness(),
            AnswerRelevancy(strictness=1),  # strictness=1 : 1 seule question generee
            LLMContextPrecisionWithoutReference(),
        ]
    except ImportError:
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        return [faithfulness, answer_relevancy, context_precision]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("TEST RAGAS — Gemini (fallback: Groq si quota epuise)")
    print("=" * 60)

    if not FICHIER_CONTEXTES.exists():
        print(f"\n[ERREUR] {FICHIER_CONTEXTES} introuvable.")
        print("  Lance d'abord : python src/reconstruire_contextes.py")
        return

    df = pd.read_csv(FICHIER_CONTEXTES, encoding="utf-8")
    echantillon = df.sample(
        n=min(TAILLE_PILOTE, len(df)), random_state=42
    ).reset_index(drop=True)
    print(f"\nEchantillon : {len(echantillon)} question(s)")
    print(f"Embeddings  : paraphrase-multilingual-MiniLM-L12-v2 (local)\n")

    try:
        llm_ragas = creer_llm_ragas(verbose=True)
    except EnvironmentError as e:
        print(f"\n[ERREUR] {e}")
        return

    donnees = {
        "question": echantillon["question"].tolist(),
        "answer": echantillon["reponse"].tolist(),
        "contexts": [
            [
                contexte[:TAILLE_MAX_CONTEXTE_CARACTERES]
                for contexte in str(contextes).split("\n\n")[:NOMBRE_CONTEXTES_EVALUES]
            ]
            for contextes in echantillon["contexte_complet"].fillna("")
        ],
    }

    # Embeddings : toujours locaux (HuggingFace)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    from ragas.embeddings import LangchainEmbeddingsWrapper
    embeddings_ragas = LangchainEmbeddingsWrapper(embeddings)

    from ragas.run_config import RunConfig
    from ragas import evaluate

    try:
        from datasets import Dataset
        dataset_ragas = Dataset.from_dict(donnees)
    except ImportError:
        print("[ERREUR] Le module 'datasets' est requis : pip install datasets")
        return

    metriques = charger_metriques()
    print(f"Lancement RAGAS : {len(echantillon)} question(s), {len(metriques)} metriques...")
    print("(Gemini en priorite, Groq en fallback automatique)\n")

    debut = time.time()
    try:
        resultats = evaluate(
            dataset_ragas,
            metrics=metriques,
            llm=llm_ragas,
            embeddings=embeddings_ragas,
            raise_exceptions=False,
            run_config=RunConfig(
                timeout=DELAI_RAGAS_SECONDES,
                max_retries=3,
                max_wait=120,
                max_workers=TRAVAILLEURS_RAGAS,
            ),
        )
    except Exception as e:
        print(f"\n[ERREUR] lors de l'evaluation RAGAS : {e}")
        import traceback
        traceback.print_exc()
        return

    duree = time.time() - debut

    print(f"\n{'=' * 60}")
    print(f"[OK] Temps total : {duree:.1f}s ({duree/len(echantillon):.1f}s/question)")
    print(f"{'=' * 60}\n")

    print("Resultats RAGAS :")
    print(resultats)

    df_resultats = resultats.to_pandas()
    df_resultats.to_csv(FICHIER_SORTIE, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Resultats sauvegardes dans : {FICHIER_SORTIE}")


if __name__ == "__main__":
    main()