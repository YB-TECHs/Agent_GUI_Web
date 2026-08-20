# src/storage/stockage.py
import sqlite3
from pathlib import Path
 
import pandas as pd
 
 
def sauvegarder(df: pd.DataFrame, chemin_base: str, formats: tuple = ('json', 'csv', 'sqlite')) -> dict:
    """
    Sauvegarde un DataFrame dans les formats demandés.
    chemin_base : chemin sans extension, ex. 'data/processed/ybtechs_scraping'.
    Retourne un dict {format: chemin_ecrit}.
    """
    Path(chemin_base).parent.mkdir(parents=True, exist_ok=True)
    chemins = {}
 
    if 'json' in formats:
        chemin = f'{chemin_base}.json'
        df.to_json(chemin, orient='records', force_ascii=False, indent=2)
        chemins['json'] = chemin
 
    if 'csv' in formats:
        chemin = f'{chemin_base}.csv'
        df.to_csv(chemin, index=False, encoding='utf-8-sig')
        chemins['csv'] = chemin
 
    if 'sqlite' in formats:
        chemin = f'{chemin_base}.db'
        with sqlite3.connect(chemin) as conn:
            df.to_sql('donnees_collectees', conn, if_exists='replace', index=False)
        chemins['sqlite'] = chemin
 
    return chemins
