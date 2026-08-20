# src/orchestrator_layer/pipeline_orchestre.py
import json, os, logging
from datetime import datetime
from bs4 import BeautifulSoup

from src.selenium_layer.navigator import create_driver, close_driver
from src.selenium_layer.waiter import wait_for_element
from src.selenium_layer.image_extractor import extraire_images_contenu, analyser_images_page
from src.ocr_layer.ocr_engine import lire_image
from src.ocr_layer.pipeline_ocr import classifier_texte
from src.omniparser_layer.omni_engine import analyser_screenshot
from src.omniparser_layer.omni_extractor import classifier_elements_ui
from src.orchestrator_layer.llm_classifier import (
    classifier_requete, resultats_non_vides, formuler_reponse, corriger_texte_ocr,
)

logger = logging.getLogger(__name__)


def pipeline_oriente(url: str, question: str) -> dict:
    """
    Cascade : Selenium (texte DOM) → images du DOM via OmniParser (SEULEMENT
    si le texte seul est insuffisant) → OCR pleine page → OmniParser pleine
    page (dernier recours). Chrome est fermé dès que le DOM est capturé,
    avant toute analyse d'image ou tout appel LLM.
    """
    prediction = classifier_requete(question, url)
    driver = create_driver(headless=True)
    screenshot = 'data/raw/screenshot_temp.png'
    resultats = {}
    urls_images = []
    texte_seul_suffisant = False

    try:
        driver.get(url)
        wait_for_element(driver, 'body', timeout=15)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        texte_html = soup.get_text(separator=' ', strip=True)
        titres = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])
                  if h.get_text(strip=True)][:8]
        reseaux = {p: a['href'] for a in soup.find_all('a', href=True)
                   for p in ['linkedin', 'facebook', 'github', 'twitter', 'instagram']
                   if p in a['href'].lower()}

        resultats = classifier_texte(texte_html)
        resultats['IDENTITE'] = titres
        resultats['RESEAUX_SOCIAUX'] = reseaux
        texte_seul_suffisant = resultats_non_vides(resultats)

        # Le texte DOM seul est insuffisant : on prépare la suite (images
        # du DOM + screenshot) PENDANT que Chrome est encore ouvert.
        if not texte_seul_suffisant:
            urls_images = extraire_images_contenu(soup, url)
            os.makedirs('data/raw', exist_ok=True)
            driver.save_screenshot(screenshot)
    finally:
        close_driver(driver)  # Chrome fermé ICI — avant images, OCR, OmniParser, LLM

    # ── Texte DOM seul suffisant : chemin rapide, rien d'autre à faire ──
    if texte_seul_suffisant:
        reponse = formuler_reponse(resultats, question)
        return _construire_sortie(url, question, 'selenium', resultats,
                                   prediction, reponse, erreur_llm=(reponse is None))

    # ── Texte DOM insuffisant : tenter de compléter avec ses images ──
    if urls_images:
        resultats['IMAGES_DETECTEES'] = analyser_images_page(urls_images)
        if resultats['IMAGES_DETECTEES']:
            logger.info(f"{len(resultats['IMAGES_DETECTEES'])} image(s) du DOM ont fourni du contenu")

    if resultats_non_vides(resultats):
        reponse = formuler_reponse(resultats, question)
        return _construire_sortie(url, question, 'selenium', resultats,
                                   prediction, reponse, erreur_llm=(reponse is None))

    logger.info("Selenium (texte + images du DOM) insuffisant → fallback OCR")

    # ── Étage 2 : OCR sur la capture pleine page ──────────
    ocr_result = lire_image(screenshot)
    resultats_ocr_brut = classifier_texte(ocr_result['texte'])
    logger.info(f"OCR brut (confiance={ocr_result['confiance']}) → nettoyage intelligent")

    texte_corrige = None
    if ocr_result['texte'].strip():
        texte_corrige = corriger_texte_ocr(ocr_result['texte'])

    if texte_corrige:
        reponse = formuler_reponse(texte_corrige, question)
        return _construire_sortie(
            url, question, 'ocr', resultats_ocr_brut, prediction, reponse,
            erreur_llm=(reponse is None),
            extra={
                'texte_ocr_brut': ocr_result['texte'],
                'texte_ocr_corrige': texte_corrige,
                'confiance_ocr': ocr_result['confiance'],
            },
        )
    logger.info("OCR : texte incompréhensible même après correction → fallback OmniParser")

    # ── Étage 3 : OmniParser pleine page (dernier recours) ──
    elements = analyser_screenshot(screenshot)
    resultats_omni = classifier_elements_ui(elements)
    reponse = formuler_reponse(resultats_omni, question)
    return _construire_sortie(url, question, 'omniparser', resultats_omni,
                               prediction, reponse, erreur_llm=(reponse is None))


def _construire_sortie(url, question, source, resultats, prediction,
                        reponse_finale, erreur_llm=False, extra: dict | None = None) -> dict:
    sortie = {
        'question': question, 'url': url, 'source': source,
        'timestamp': datetime.now().isoformat(),
        'resultats': resultats,
        'reponse_finale': reponse_finale,
        'erreur_llm': erreur_llm,
        'prediction_llm': prediction,
        'concordance': prediction['type_interface'] == source,
    }
    if extra:
        sortie.update(extra)
    os.makedirs('data/processed', exist_ok=True)
    nom = f"data/processed/oriente_{url.split('//')[-1].split('/')[0].replace('.', '_')}.json"
    with open(nom, 'w', encoding='utf-8') as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)
    return sortie