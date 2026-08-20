# tests/test_storage.py
import sqlite3
 
import pandas as pd
 
from src.storage.stockage import sauvegarder
 
 
def test_sauvegarder_trois_formats(tmp_path):
    df = pd.DataFrame([{'categorie': 'IDENTITE', 'cle': 'nom', 'valeur': 'YB-TECHs'}])
    chemins = sauvegarder(df, str(tmp_path / 'test'), formats=('json', 'csv', 'sqlite'))
    assert set(chemins) == {'json', 'csv', 'sqlite'}
    with sqlite3.connect(chemins['sqlite']) as conn:
        n = conn.execute('SELECT COUNT(*) FROM donnees_collectees').fetchone()[0]
    assert n == 1
