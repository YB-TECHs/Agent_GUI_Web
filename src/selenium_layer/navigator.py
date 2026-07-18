# src/selenium_layer/navigator.py
 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
 
def create_driver(headless: bool = False, timeout: int = 30) -> webdriver.Chrome:
    """
    Crée et retourne un driver Chrome configuré.
    
    Args:
        headless: Si True, Chrome tourne sans interface graphique
        timeout: Délai max d'attente en secondes
    Returns:
        driver: Instance Chrome prête à l'emploi
    """
    options = Options()
    
    # Mode headless : Chrome tourne en arrière-plan sans fenêtre visible
    if headless:
        options.add_argument("--headless=new")
    
    # Options essentielles pour éviter la détection anti-bot
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Taille de fenêtre standard
    options.add_argument("--window-size=1920,1080")
    
    # User-agent réaliste (simule un vrai navigateur)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Désactiver les notifications et popups gênants
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Créer le driver avec gestion automatique de ChromeDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # Timeout global : si une page met plus de 'timeout' secondes à charger
    driver.set_page_load_timeout(timeout)
    
    logger.info(f"Driver Chrome créé — headless={headless}, timeout={timeout}s")
    return driver
 
 
def close_driver(driver: webdriver.Chrome) -> None:
    """Ferme proprement le driver et libère les ressources."""
    try:
        driver.quit()
        logger.info("Driver Chrome fermé.")
    except Exception as e:
        logger.warning(f"Erreur fermeture driver : {e}")
