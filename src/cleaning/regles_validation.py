# src/cleaning/regles_validation.py
import re
 
import pandas as pd
 
REGLES = {
    'emails': lambda v: bool(re.fullmatch(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', v)),
    'telephones': lambda v: 8 <= len(re.sub(r'\D', '', v)) <= 15,
}
 
 
def valider_dataframe(df: pd.DataFrame) -> dict:
    """
    Applique les règles métier connues aux lignes concernées et retourne
    un rapport : {cle: {'valides': n, 'invalides': n, 'erreurs': [...]}}.
    """
    rapport = {}
    for cle, regle in REGLES.items():
        sous_df = df[df['cle'] == cle]
        if sous_df.empty:
            continue
        valides = sous_df['valeur'].apply(regle)
        rapport[cle] = {
            'valides': int(valides.sum()),
            'invalides': int((~valides).sum()),
            'erreurs': sous_df.loc[~valides, 'valeur'].tolist(),
        }
    return rapport
