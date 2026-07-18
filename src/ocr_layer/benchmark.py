# src/ocr_layer/benchmark.py
import time
import easyocr
import pytesseract
from PIL import Image
import pandas as pd
from src.ocr_layer.preprocessor import ameliorer_image
import logging
 
logger = logging.getLogger(__name__)
 
 
def calculer_cer(texte_predit: str, texte_reel: str) -> float:
    """Calcule le Character Error Rate (CER) entre deux textes."""
    if not texte_reel:
        return 1.0
    erreurs  = sum(c1 != c2 for c1, c2 in zip(texte_predit, texte_reel))
    erreurs += abs(len(texte_predit) - len(texte_reel))
    return round(erreurs / max(len(texte_reel), 1), 3)
 
 
def benchmarker(images: list[dict], preprocessing: bool = True) -> pd.DataFrame:
    """
    Compare EasyOCR et Tesseract sur une liste d'images.
    Args:
        images: liste de {'nom': str, 'chemin': str, 'texte_reel': str}
    Returns:
        DataFrame avec résultats de benchmark
    """
    reader     = easyocr.Reader(['fr', 'en'], gpu=False)
    resultats  = []
 
    for img_info in images:
        nom    = img_info['nom']
        chemin = img_info['chemin']
        reel   = img_info.get('texte_reel', '')
 
        img_arr = ameliorer_image(chemin) if preprocessing else None
 
        # ── EasyOCR ──────────────────────────────────────────────
        t0        = time.time()
        easy_res  = reader.readtext(img_arr if img_arr is not None else chemin)
        easy_text = ' '.join([r[1] for r in easy_res])
        easy_conf = round(sum([r[2] for r in easy_res]) / max(len(easy_res), 1), 2)
        easy_time = round(time.time() - t0, 2)
        easy_cer  = calculer_cer(easy_text, reel) if reel else None
 
        # ── Tesseract ─────────────────────────────────────────────
        t0        = time.time()
        img_pil   = Image.fromarray(img_arr) if img_arr is not None else Image.open(chemin)
        tess_text = pytesseract.image_to_string(img_pil, lang='fra+eng')
        tess_time = round(time.time() - t0, 2)
        tess_cer  = calculer_cer(tess_text, reel) if reel else None
 
        resultats.append({
            'Image'            : nom,
            'EasyOCR_CER'      : easy_cer,
            'EasyOCR_Confiance': easy_conf,
            'EasyOCR_Temps(s)' : easy_time,
            'Tesseract_CER'    : tess_cer,
            'Tesseract_Temps(s)': tess_time,
            'Meilleur'         : 'EasyOCR' if (easy_cer or 1) <= (tess_cer or 1) else 'Tesseract',
        })
 
    df = pd.DataFrame(resultats)
    df.to_csv('data/processed/benchmark_ocr.csv', index=False, encoding='utf-8-sig')
    logger.info('Benchmark sauvegardé : data/processed/benchmark_ocr.csv')
    return df
