# scripts/executer_cas_usage.py
"""Exécute le pipeline sur les cas d'usage réels et produit des
livrables permanents : JSON/CSV/SQLite par cas + un rapport PDF unique."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from pathlib import Path

import pandas as pd

from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente
from src.cleaning.nettoyeur import nettoyer
from src.cleaning.regles_validation import valider_dataframe
from src.storage.stockage import sauvegarder
from src.reports.generateur_rapport import generer_rapport_html, generer_rapport_pdf

headless = True
def executer_tous_les_cas(chemin_cas: str = 'data/tests/cas_usage_ybtechs.json') -> list[dict]:
    with open(chemin_cas, encoding='utf-8') as f:
        cas_usage = json.load(f)

    resultats_session = []
    for i, cas in enumerate(cas_usage, 1):
        print(f"[{i}/{len(cas_usage)}] {cas['url']} — {cas['question']}")
        #sortie = pipeline_oriente(cas['url'], cas['question'], headless=headless)
        sortie = pipeline_oriente(cas['url'], cas['question'], headless=headless)
        df = nettoyer(sortie)
        validation = valider_dataframe(df)  # ← résultat maintenant conservé

        chemins = sauvegarder(df, f"data/processed/cas_{i}_{sortie['source']}")

        resultats_session.append({
            'cas': cas, 'source': sortie['source'],
            'reponse_finale': sortie['reponse_finale'],
            'erreur_llm': sortie['erreur_llm'],
            'df': df, 'validation': validation,
            'nb_lignes': len(df), 'chemins': chemins,
        })
        print(f"   → source={sortie['source']} | reponse={sortie['reponse_finale']!r}")

    return resultats_session


def generer_rapport_session(resultats_session: list[dict]) -> None:
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
        source='Session de tests — Semaine 7', df=df_session, validation=validation_session,
        chemin_sortie='data/processed/rapport_semaine7.html',
    )
    generer_rapport_pdf(chemin_html, 'data/processed/rapport_semaine7.pdf')
    print("\n✅ Rapport permanent : data/processed/rapport_semaine7.pdf")

if __name__ == '__main__':
    resultats = executer_tous_les_cas()
    generer_rapport_session(resultats)