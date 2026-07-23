# src/omniparser_layer/pipeline_omni.py
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json, os, logging
from datetime import datetime
from src.selenium_layer.navigator import create_driver, close_driver
from src.selenium_layer.waiter import wait_for_element
from src.ocr_layer.ocr_engine import lire_image
from src.ocr_layer.pipeline_ocr import classifier_texte
from src.omniparser_layer.omni_engine import analyser_screenshot
from src.omniparser_layer.omni_extractor import classifier_elements_ui
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)
 
SEUIL_HTML = 100  # chars minimum pour Selenium
SEUIL_OCR  = 30   # chars minimum pour l'OCR
 
 
def pipeline_tri_couche(url: str, question: str) -> dict:
    """
    Pipeline aveugle complet : Selenium → OCR → OmniParser.
    L'utilisateur pose une question, le pipeline choisit la couche.
    """
    driver = create_driver(headless=True)
    source = 'selenium'
    resultats = {}
 
    try:
        driver.get(url)
        wait_for_element(driver, 'body', timeout=15)
 
        soup   = BeautifulSoup(driver.page_source, 'lxml')
        texte  = soup.get_text(separator=' ', strip=True)
        titres = [h.get_text(strip=True) for h in soup.find_all(['h1','h2','h3']) if h.get_text(strip=True)][:8]
        reseaux= {p: a['href'] for a in soup.find_all('a', href=True)
                  for p in ['linkedin','facebook','github','twitter'] if p in a['href'].lower()}
 
        # ── Couche 1 : Selenium ───────────────────────────────
        if len(texte.strip()) > SEUIL_HTML:
            logger.info(f'Couche 1 (Selenium) : {len(texte)} chars')
            source    = 'selenium'
            resultats = classifier_texte(texte)
            resultats['IDENTITE']        = titres
            resultats['RESEAUX_SOCIAUX'] = reseaux
 
        else:
            # Prendre un screenshot pour OCR et OmniParser
            os.makedirs('data/raw', exist_ok=True)
            screenshot = 'data/raw/screenshot_temp.png'
            driver.save_screenshot(screenshot)
 
            # ── Couche 2 : OCR ────────────────────────────────
            ocr_result = lire_image(screenshot)
            texte_ocr  = ocr_result['texte']
 
            if len(texte_ocr.strip()) > SEUIL_OCR:
                logger.info(f'Couche 2 (OCR) : {len(texte_ocr)} chars')
                source    = 'ocr'
                resultats = classifier_texte(texte_ocr)
 
            else:
                # ── Couche 3 : OmniParser ─────────────────────
                logger.info('Couche 3 (OmniParser) : analyse GUI')
                source    = 'omniparser'
                elements  = analyser_screenshot(screenshot)
                resultats = classifier_elements_ui(elements)
 
        sortie = {
            'question' : question,
            'url'      : url,
            'source'   : source,
            'timestamp': datetime.now().isoformat(),
            'resultats': resultats,
        }
 
        os.makedirs('data/processed', exist_ok=True)
        nom = f"data/processed/tricouche_{url.split('//')[-1].split('/')[0].replace('.','_')}.json"
        with open(nom, 'w', encoding='utf-8') as f:
            json.dump(sortie, f, ensure_ascii=False, indent=2)
        logger.info(f'Résultats → {nom}')
        return sortie
 
    finally:
        close_driver(driver)

