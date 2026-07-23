# src/omniparser_layer/omni_engine.py
import sys, os, json
import logging
from PIL import Image
 
logger = logging.getLogger(__name__)
 
# Ajoute le dossier OmniParser au path Python
OMNI_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'OmniParser')
sys.path.insert(0, os.path.abspath(OMNI_PATH))
 
_model = None  # Chargé une seule fois
 
def _get_model():
    """Charge les modèles OmniParser une seule fois."""
    global _model
    if _model is None:
        try:
            from util.utils import get_yolo_model, get_caption_model_processor
            weights = os.path.join(OMNI_PATH, 'weights')
            yolo    = get_yolo_model(os.path.join(weights, 'icon_detect', 'model.pt'))
            caption = get_caption_model_processor(
                model_name='florence2',
                model_name_or_path=os.path.join(weights, 'icon_caption_florence')
            )
            _model  = {'yolo': yolo, 'caption': caption}
            logger.info('OmniParser chargé avec succès.')
        except Exception as e:
            logger.error(f'Échec chargement OmniParser : {e}')
            raise
    return _model
 
 
def analyser_screenshot(chemin_image: str) -> list[dict]:
    """
    Analyse un screenshot avec OmniParser v2.
    Args:
        chemin_image : chemin vers le screenshot PNG
    Returns:
        Liste de dicts : {type, texte, coordonnees, confiance}
    """
    if not os.path.isfile(chemin_image):
        raise FileNotFoundError(f'Image introuvable : {chemin_image}')
 
    model = _get_model()
 
    try:
        from util.utils import get_som_labeled_img, check_ocr_box
        image = Image.open(chemin_image)
 
        # Appel OmniParser : détection YOLO + description Florence-2
        box_threshold = 0.05
        ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
            chemin_image, display_img=False,
            output_bb_format='xyxy', goal_filtering=None,
            easyocr_args={'paragraph': False, 'text_threshold': 0.9}
        )
        #text_local, _ = ocr_bbox_rslt
        text_local, ocr_bbox = ocr_bbox_rslt
 
        dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
            chemin_image, model['yolo'],
            BOX_TRESHOLD=box_threshold,
            output_coord_in_ratio=False,
            #ocr_bbox=text_local,
            ocr_bbox=ocr_bbox,
            caption_model_processor=model['caption'],
            ocr_text=text_local,
            iou_threshold=0.1
        )
 
        elements = []
        for i, item in enumerate(parsed_content_list):
            coord = label_coordinates.get(str(i+1), [0,0,0,0])
            elements.append({
                'type'       : 'ui_element',
                'texte'      : str(item),
                'coordonnees': coord,
                'index'      : i + 1,
            })
 
        logger.info(f'OmniParser : {len(elements)} éléments détectés.')
        return elements
 
    except Exception as e:
        logger.error(f'Erreur OmniParser : {e}')
        return []
