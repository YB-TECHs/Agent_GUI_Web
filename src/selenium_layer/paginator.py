# src/selenium_layer/paginator.py
 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from src.selenium_layer.waiter import wait_for_clickable
import logging
import time
 
logger = logging.getLogger(__name__)
 
 
def click_next_button(driver: webdriver.Chrome,
                      next_selector: str = 'li.next a') -> bool:
    """
    Clique sur le bouton 'Page suivante'.
    Returns: True si le clic a réussi, False si plus de page suivante.
    """
    button = wait_for_clickable(driver, next_selector, timeout=5)
    if button:
        button.click()
        time.sleep(1)  # Petite pause pour laisser la page se charger
        logger.info("Page suivante chargée.")
        return True
    logger.info("Plus de page suivante — fin de la pagination.")
    return False
 
 
def scrape_all_pages(driver: webdriver.Chrome,
                     extract_func,
                     next_selector: str = 'li.next a',
                     max_pages: int = 10) -> list:
    """
    Applique extract_func sur chaque page et accumule les résultats.
    
    Args:
        driver: Le driver Chrome (déjà positionné sur la page 1)
        extract_func: Fonction qui extrait les données d'une page
                      Elle doit prendre driver en argument et retourner une liste
        next_selector: Sélecteur CSS du bouton 'Suivant'
        max_pages: Nombre maximum de pages à parcourir (sécurité)
    Returns:
        Liste complète de tous les éléments extraits
    """
    all_results = []
    page = 1
    
    while page <= max_pages:
        logger.info(f"Extraction page {page}...")
        results = extract_func(driver)
        all_results.extend(results)
        logger.info(f"  → {len(results)} éléments extraits sur cette page.")
        
        # Essaie d'aller à la page suivante
        if not click_next_button(driver, next_selector):
            break  # Plus de page suivante
        page += 1
    
    logger.info(f"Pagination terminée : {page} page(s), {len(all_results)} éléments au total.")
    return all_results
