# src/selenium_layer/waiter.py
 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import logging
 
logger = logging.getLogger(__name__)
 
 
def wait_for_element(driver: webdriver.Chrome, selector: str,
                     by: str = 'css', timeout: int = 15):
    """
    Attend qu'un élément soit présent et visible dans la page.
    
    Args:
        driver: Le driver Chrome
        selector: Le sélecteur CSS ou XPath de l'élément
        by: 'css' pour CSS selector, 'xpath' pour XPath
        timeout: Nombre de secondes max à attendre
    Returns:
        L'élément WebElement trouvé, ou None si timeout
    """
    by_type = By.CSS_SELECTOR if by == 'css' else By.XPATH
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_type, selector))
        )
        logger.info(f"Élément trouvé : {selector}")
        return element
    except TimeoutException:
        logger.warning(f"Timeout : élément {selector} non trouvé après {timeout}s")
        return None
 
 
def wait_for_table(driver: webdriver.Chrome, timeout: int = 15):
    """Attend qu'un tableau HTML <table> soit présent dans la page."""
    return wait_for_element(driver, 'table', timeout=timeout)
 
 
def wait_for_text(driver: webdriver.Chrome, selector: str,
                  text: str, timeout: int = 15) -> bool:
    """Attend qu'un texte précis apparaisse dans un élément."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, selector), text
            )
        )
        return True
    except TimeoutException:
        return False
 
 
def wait_for_clickable(driver: webdriver.Chrome, selector: str,
                       timeout: int = 15):
    """Attend qu'un bouton soit cliquable."""
    by_type = By.CSS_SELECTOR
    try:
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by_type, selector))
        )
    except TimeoutException:
        logger.warning(f"Bouton {selector} non cliquable après {timeout}s")
        return None
