# src/reports/generateur_rapport.py
from datetime import datetime
from pathlib import Path
 
from jinja2 import Environment, FileSystemLoader
 
DOSSIER_TEMPLATES = Path(__file__).parent / 'templates'
 
 
def generer_rapport_html(source: str, df, validation: dict, chemin_sortie: str) -> str:
    env = Environment(loader=FileSystemLoader(str(DOSSIER_TEMPLATES)))
    template = env.get_template('rapport.html.jinja')
    html = template.render(
        source=source,
        timestamp=datetime.now().strftime('%d/%m/%Y %H:%M'),
        nb_lignes=len(df),
        nb_categories=df['categorie'].nunique() if not df.empty else 0,
        validation=validation,
        lignes=df.to_dict('records') if not df.empty else [],  # ← ajouté
    )
    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(chemin_sortie).write_text(html, encoding='utf-8')
    return chemin_sortie
 
def generer_rapport_pdf(chemin_html: str, chemin_pdf: str) -> str:
    """
    Génère le PDF via Chrome headless (impression native), en réutilisant
    Selenium déjà installé et fiabilisé — évite la dépendance fragile à
    WeasyPrint/GTK3 sous Windows (conflit de DLL avec Tesseract-OCR).
    """
    import base64
    from pathlib import Path
    from src.selenium_layer.navigator import create_driver, close_driver

    chemin_absolu = Path(chemin_html).resolve().as_uri()
    driver = create_driver(headless=True)
    try:
        driver.get(chemin_absolu)
        resultat = driver.execute_cdp_cmd('Page.printToPDF', {'printBackground': True})
        Path(chemin_pdf).write_bytes(base64.b64decode(resultat['data']))
    finally:
        close_driver(driver)
    return chemin_pdf
