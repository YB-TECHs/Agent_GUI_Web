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
    )
    Path(chemin_sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(chemin_sortie).write_text(html, encoding='utf-8')
    return chemin_sortie
 
 
def generer_rapport_pdf(chemin_html: str, chemin_pdf: str) -> str:
    from weasyprint import HTML  # import local : évite l'erreur si GTK3 absent
    HTML(chemin_html).write_pdf(chemin_pdf)
    return chemin_pdf
