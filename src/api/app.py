# src/api/app.py
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

from src.cleaning.nettoyeur import nettoyer
from src.cleaning.regles_validation import valider_dataframe
from src.reports.generateur_rapport import generer_rapport_html, generer_rapport_pdf

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

from src.orchestrator_layer.memoire_conversation import obtenir_historique


@app.get("/historique")
def historique():
    """Retourne l'historique de conversation (jusqu'à 100 derniers messages)."""
    return {"messages": obtenir_historique()}


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

def lire_cas_usage(chemin: Path) -> list[dict]:
    """Lit un fichier .xlsx/.xls ou .json et retourne [{'url':..., 'question':...}]."""
    suffixe = chemin.suffix.lower()
    if suffixe == '.json':
        with open(chemin, encoding='utf-8') as f:
            data = json.load(f)
        return [{'url': str(d['url']).strip(), 'question': str(d['question']).strip()} for d in data]
    elif suffixe in ('.xlsx', '.xls'):
        df = pd.read_excel(chemin)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return [{'url': str(r['url']).strip(), 'question': str(r['question']).strip()} for _, r in df.iterrows()]
    raise ValueError("Format non supporté — utilise .xlsx ou .json")


@app.post("/api/traiter-chaine")
async def traiter_chaine(fichier: UploadFile = File(...)):
    suffixe = Path(fichier.filename).suffix.lower()
    if suffixe not in ('.xlsx', '.xls', '.json'):
        return JSONResponse(status_code=400, content={"erreur": "Format non supporté. Utilise .xlsx ou .json."})

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffixe) as tmp:
        shutil.copyfileobj(fichier.file, tmp)
        chemin_tmp = Path(tmp.name)

    try:
        cas_usage = lire_cas_usage(chemin_tmp)
    except Exception as e:
        return JSONResponse(status_code=400, content={"erreur": f"Fichier illisible : {e}"})
    finally:
        chemin_tmp.unlink(missing_ok=True)

    if not cas_usage:
        return JSONResponse(status_code=400, content={"erreur": "Aucun cas d'usage trouvé dans le fichier."})

    resultats_session = []
    for cas in cas_usage:
        try:
            sortie = pipeline_oriente(cas['url'], cas['question'])
            df = nettoyer(sortie)
            validation = valider_dataframe(df)
        except Exception as e:
            df = pd.DataFrame([{'categorie': 'ERREUR', 'cle': 'exception', 'valeur': str(e)}])
            sortie = {'reponse_finale': None}
            validation = {}
        resultats_session.append({'cas': cas, 'reponse_finale': sortie.get('reponse_finale'), 'df': df, 'validation': validation})

    lignes = []
    validation_session = {}
    for i, r in enumerate(resultats_session, 1):
        label_cas = f"Cas {i} — {r['cas']['url']} — {r['cas']['question']}"
        lignes.append({'categorie': 'REPONSE', 'cle': label_cas, 'valeur': r['reponse_finale'] or '(pas de réponse)'})
        for _, ligne in r['df'].iterrows():
            lignes.append({'categorie': f"CAS{i}_{ligne['categorie']}", 'cle': ligne['cle'], 'valeur': ligne['valeur']})
        for categorie, stats in r['validation'].items():
            validation_session[f"CAS{i}_{categorie}"] = stats

    df_session = pd.DataFrame(lignes)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    chemin_html = generer_rapport_html(
        source='Extraction en chaîne', df=df_session, validation=validation_session,
        chemin_sortie='data/processed/rapport_chaine.html',
    )
    chemin_pdf = generer_rapport_pdf(chemin_html, 'data/processed/rapport_chaine.pdf')

    return FileResponse(chemin_pdf, media_type='application/pdf', filename='rapport_chaine.pdf')

app.mount("/", StaticFiles(directory="src/api/static", html=True), name="static")