"""
Test RAGAS avec reponses de REFERENCE (ground truth manuel).
Utilise le fallback automatique Gemini -> Groq si quota epuise.
"""

import json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import ragas_compat  # noqa: F401
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas_llm_factory import creer_llm_ragas
from rag_agent import EMBEDDING_MODEL

FICHIER_CAS     = Path("data/processed/reference_test_cases.json")
FICHIER_DATASET = Path("data/processed/dataset_final_nettoye.csv")
FICHIER_SORTIE  = Path("data/processed/ragas_reference_resultats.csv")
DELAI = 300

def main():
    print("=" * 60)
    print("TEST RAGAS — REFERENCES MANUELLES")
    print("Metrique : AnswerCorrectness (RAG vs bonne reponse)")
    print("Fallback : Gemini -> Groq automatique")
    print("=" * 60)

    with open(FICHIER_CAS, encoding="utf-8") as f:
        cas = json.load(f)

    df = pd.read_csv(FICHIER_DATASET, encoding="utf-8-sig")
    rag_par_id = df.set_index("id")["reponse"].to_dict()

    questions, references, reponses_rag, ids = [], [], [], []
    print()
    for c in cas:
        rag_rep = rag_par_id.get(c["id"], "")
        if not rag_rep:
            print(f"  /!\\ ID {c['id']} absent du dataset, ignore.")
            continue
        questions.append(c["question"])
        references.append(c["reponse_reference"])
        reponses_rag.append(str(rag_rep))
        ids.append(c["id"])
        print(f"  [{c['id']}] {c['question']}")
        print(f"    RAG : {str(rag_rep)[:120]}...")
        print(f"    REF : {c['reponse_reference'][:120]}...")
        print()

    from datasets import Dataset
    from ragas.metrics import AnswerCorrectness
    from ragas.run_config import RunConfig
    from ragas import evaluate

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": reponses_rag,
        "reference": references,
    })

    print("Initialisation des providers LLM :")
    try:
        llm_ragas = creer_llm_ragas(verbose=True)
    except EnvironmentError as e:
        print(f"\n[ERREUR] {e}")
        return

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    emb_ragas  = LangchainEmbeddingsWrapper(embeddings)

    print(f"\nLancement : {len(questions)} questions x 1 metrique (AnswerCorrectness)...")
    print(f"Quota consomme : {len(questions)} requetes\n")

    debut = time.time()
    resultats = evaluate(
        dataset,
        metrics=[AnswerCorrectness()],
        llm=llm_ragas,
        embeddings=emb_ragas,
        raise_exceptions=False,
        run_config=RunConfig(timeout=DELAI, max_retries=3, max_wait=120, max_workers=1),
    )
    duree = time.time() - debut

    print(f"\n{'='*60}")
    print(f"[OK] Temps total : {duree:.1f}s ({duree/len(questions):.1f}s/question)")
    print(f"{'='*60}\n")

    df_res = resultats.to_pandas()
    df_res.insert(0, "id", ids)
    df_res["question"]          = questions
    df_res["reponse_rag"]       = reponses_rag
    df_res["reponse_reference"] = references

    print("Resultats AnswerCorrectness :")
    print(df_res[["id", "question", "answer_correctness"]].to_string(index=False))

    df_res.to_csv(FICHIER_SORTIE, index=False, encoding="utf-8-sig")
    print(f"\n[OK] Resultats sauvegardes dans : {FICHIER_SORTIE}")

if __name__ == "__main__":
    main()
