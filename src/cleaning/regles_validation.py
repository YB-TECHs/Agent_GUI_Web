# src/cleaning/regles_validation.py
import re
 
import pandas as pd
 
REGLES = {
    'CONTACTS_EMAIL': lambda v: bool(re.fullmatch(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', v)),
    'CONTACTS_TEL': lambda v: 8 <= len(re.sub(r'\D', '', v)) <= 15,
}
 
 
def valider_dataframe(df: pd.DataFrame) -> dict:
    """
    Applique les règles métier connues, filtrées par CATEGORIE réelle
    (pas par cle). Retourne {categorie: {'valides', 'invalides', 'erreurs'}}.
    """
    rapport = {}
    for categorie, regle in REGLES.items():
        sous_df = df[df['categorie'] == categorie]
        if sous_df.empty:
            continue
        valides = sous_df['valeur'].apply(regle)
        rapport[categorie] = {
            'valides': int(valides.sum()),
            'invalides': int((~valides).sum()),
            'erreurs': sous_df.loc[~valides, 'valeur'].tolist(),
        }
    return rapport
