# src/ocr_layer/pipeline_ocr.py
import json, re, os
from datetime import datetime
from src.selenium_layer.navigator import create_driver, close_driver
from src.selenium_layer.waiter import wait_for_element
from src.ocr_layer.ocr_engine import lire_image
from bs4 import BeautifulSoup
import logging
 
logger = logging.getLogger(__name__)
 
SEUIL_TEXTE_HTML = 100  # Moins de 100 chars → fallback OCR
 
 
def classifier_texte(texte: str) -> dict:
    """Classification aveugle en 7 catégories — identique au pipeline S2."""
    soup_text = texte  # Texte brut (HTML ou OCR)
    return {
        'CONTACTS_EMAIL'   : list(set(re.findall(r'[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}', soup_text))),
        'CONTACTS_TEL'     : list(set(re.findall(r'\+?\d[\d\s\-().]{7,15}\d', soup_text)))[:5],
        'LOCALISATION'     : list(set(re.findall(r'\b(?:rue|avenue|boulevard|city|cedex|bp|po box|\d{4,6})\b.{0,60}', soup_text.lower())))[:5],
        'IDENTITE'         : [],  # Rempli via soup si dispo
        'INFORMATIONS'     : [p for p in soup_text.split('.') if 30 < len(p.strip()) < 250][:5],
    }
 
 
def pipeline_aveugle(url: str, question: str) -> dict:
    """
    Pipeline aveugle complet S2 + S3.
    1. Selenium tente le HTML
    2. Si texte insuffisant → screenshot → OCR
    3. Classification identique dans les deux cas
    """
    driver  = create_driver(headless=True)
    source  = 'selenium'
 
    try:
        driver.get(url)
        wait_for_element(driver, 'body', timeout=15)
 
        soup     = BeautifulSoup(driver.page_source, 'lxml')
        texte    = soup.get_text(separator=' ', strip=True)
        titres   = [h.get_text(strip=True) for h in soup.find_all(['h1','h2','h3']) if h.get_text(strip=True)][:8]
        reseaux  = {p: a['href'] for a in soup.find_all('a', href=True)
                    for p in ['linkedin','facebook','github','twitter','instagram']
                    if p in a['href'].lower()}
 
        # ── Décision : HTML suffisant ? ─────────────────────────
        if len(texte.strip()) <= SEUIL_TEXTE_HTML:
            logger.info(f'Texte HTML insuffisant ({len(texte)} chars) → fallback OCR')
            source = 'ocr'
            screenshot = 'data/raw/screenshot_temp.png'
            os.makedirs('data/raw', exist_ok=True)
            driver.save_screenshot(screenshot)
            ocr_result  = lire_image(screenshot)
            texte       = ocr_result['texte']
            titres      = []
            reseaux     = {}
        else:
            logger.info(f'Texte HTML suffisant ({len(texte)} chars) → pipeline Selenium')
 
        resultats             = classifier_texte(texte)
        resultats['IDENTITE'] = titres
        resultats['RESEAUX_SOCIAUX'] = reseaux
 
        sortie = {
            'question' : question,
            'url'      : url,
            'source'   : source,
            'timestamp': datetime.now().isoformat(),
            'resultats': resultats,
        }
 
        # Sauvegarde JSON
        os.makedirs('data/processed', exist_ok=True)
        nom = f"data/processed/pipeline_{url.split('//')[-1].split('/')[0].replace('.','_')}.json"
        with open(nom, 'w', encoding='utf-8') as f:
            json.dump(sortie, f, ensure_ascii=False, indent=2)
        logger.info(f'Résultats sauvegardés : {nom}')
        return sortie
 
    finally:
        close_driver(driver)
