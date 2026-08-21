# scripts/benchmark_kpis.py
import json
import time
from collections import Counter
from pathlib import Path
 
from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente
 
 
def mesurer_kpis(cas_usage: list[dict]) -> dict:
    couches_utilisees = Counter()
    temps_par_cas = []
    echecs_techniques = 0
    reponses_manquantes = 0
 
    for cas in cas_usage:
        debut = time.perf_counter()
        try:
            sortie = pipeline_oriente(cas['url'], cas['question'])
            couches_utilisees[sortie['source']] += 1
            if sortie['erreur_llm'] or not sortie['reponse_finale']:
                reponses_manquantes += 1
        except Exception:
            echecs_techniques += 1
        temps_par_cas.append(time.perf_counter() - debut)
 
    nb_cas = len(cas_usage)
    taux_reussite_technique = round((nb_cas - echecs_techniques) / nb_cas, 3) if nb_cas else 0.0
    taux_reponse_formulee = round((nb_cas - reponses_manquantes) / nb_cas, 3) if nb_cas else 0.0
    temps_moyen = round(sum(temps_par_cas) / len(temps_par_cas), 2) if temps_par_cas else 0.0
 
    return {
        'nb_cas_testes': nb_cas,
        'taux_reussite_technique': taux_reussite_technique,
        'taux_reponse_formulee': taux_reponse_formulee,
        'temps_moyen_secondes': temps_moyen,
        'repartition_couches': dict(couches_utilisees),
        'cible_cdc_temps_moyen_s': 30,
        'cible_cdc_taux_extraction': 0.90,
    }
 
 
if __name__ == '__main__':
    with open('data/tests/cas_usage_ybtechs.json', encoding='utf-8') as f:
        cas_usage = json.load(f)
    kpis = mesurer_kpis(cas_usage)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    with open('data/processed/benchmark_kpis.json', 'w', encoding='utf-8') as f:
        json.dump(kpis, f, ensure_ascii=False, indent=2)
    print(json.dumps(kpis, ensure_ascii=False, indent=2))
