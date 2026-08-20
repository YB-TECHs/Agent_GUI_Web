import logging
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

def extraire_images_contenu(soup, url_page: str, seuil_px: int = 200, max_images: int = 2) -> list[str]:
    """Repère les images du DOM assez grandes pour probablement contenir de l'info."""
    images, vues = [], set()
    for img in soup.find_all('img'):
        largeur, hauteur = img.get('width'), img.get('height')
        try:
            if largeur and hauteur and (int(largeur) < seuil_px or int(hauteur) < seuil_px):
                continue
        except ValueError:
            pass
        src = img.get('src')
        if src:
            url_absolue = urljoin(url_page, src)
            if url_absolue not in vues:
                vues.add(url_absolue)
                images.append(url_absolue)
    return images[:max_images]


def analyser_images_page(urls_images: list[str]) -> list[dict]:
    """
    Analyse chaque image du DOM via OmniParser. Retourne une liste
    structurée par image (pas fusionnée dans les catégories du DOM),
    pour que la provenance de chaque élément reste explicite quand
    Phi-3 lit ces résultats.
    """
    from src.omniparser_layer.omni_engine import analyser_screenshot
    from src.omniparser_layer.omni_extractor import classifier_elements_ui

    resultats_par_image = []
    for i, url_img in enumerate(urls_images):
        try:
            chemin = f'data/raw/img_page_{i}.png'
            reponse = requests.get(url_img, timeout=10)
            reponse.raise_for_status()
            with open(chemin, 'wb') as f:
                f.write(reponse.content)

            elements = analyser_screenshot(chemin)
            if elements:
                classes = classifier_elements_ui(elements)
                contenu = {cat: val for cat, val in classes.items() if val}
                if contenu:
                    resultats_par_image.append({'url_image': url_img, 'contenu': contenu})
        except Exception as e:
            logger.warning(f"Analyse OmniParser de l'image {url_img} impossible ({e})")
    return resultats_par_image