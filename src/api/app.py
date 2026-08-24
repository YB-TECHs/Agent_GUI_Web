# src/api/app.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente

app = FastAPI(title="YB-TECHs Agent Pipeline")


from datetime import datetime

from src.orchestrator_layer.llm_classifier import repondre_discussion


class Requete(BaseModel):
    url: str = ""
    question: str


@app.post("/analyser")
def analyser(requete: Requete):
    url = requete.url.strip()

    if not url:
        reponse = repondre_discussion(requete.question)
        return {
            'question': requete.question, 'url': None, 'source': 'discussion',
            'timestamp': datetime.now().isoformat(),
            'resultats': {}, 'reponse_finale': reponse,
            'erreur_llm': reponse is None,
            'prediction_llm': None, 'concordance': None,
        }

    return pipeline_oriente(url, requete.question)

app.mount("/", StaticFiles(directory="src/api/static", html=True), name="static")