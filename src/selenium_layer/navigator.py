# src/selenium_layer/navigator.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_driver(headless: bool = False, timeout: int = 30) -> webdriver.Chrome:
    """Crée et retourne un driver Chrome configuré."""
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    # Charge le DOM sans attendre toutes les ressources tierces (images,
    # trackers...) — réduit les timeouts sur des pages avec ressources lentes.
    options.page_load_strategy = 'eager'

    driver = webdriver.Chrome(
        service=Service(executable_path=r"E:\NIVEAU4\Stage\Projet1\drivers\chromedriver.exe"),
        options=options
    )

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