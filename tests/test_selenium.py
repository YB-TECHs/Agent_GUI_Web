# tests/test_selenium.py
 
import pytest
import sys
sys.path.insert(0, r'E:\NIVEAU4\Stage\Projet1')
 
from src.selenium_layer.navigator import create_driver, close_driver
from src.selenium_layer.waiter import wait_for_element
from src.selenium_layer.extractor import extract_links, extract_text_by_selector
from src.selenium_layer.paginator import click_next_button
 
 
# ── FIXTURE : crée un driver partagé pour tous les tests ──────────
@pytest.fixture(scope='module')
def driver():
    """Crée un driver Chrome pour les tests — se ferme après tous les tests."""
    d = create_driver(headless=True)
    yield d  # Les tests s'exécutent ici
    close_driver(d)
 
 
# ── TEST 1 : le driver se crée sans erreur ────────────────────────
def test_driver_creation():
    """Vérifie que le driver Chrome se crée correctement."""
    d = create_driver(headless=True)
    assert d is not None
    close_driver(d)
 
 
# ── TEST 2 : navigation vers une URL ─────────────────────────────
def test_navigation(driver):
    """Vérifie que Selenium peut charger une page web."""
    driver.get('https://books.toscrape.com')
    assert 'Books' in driver.title
 
 
# ── TEST 3 : attente d'un élément ────────────────────────────────
def test_wait_for_element(driver):
    """Vérifie que wait_for_element trouve un élément existant."""
    driver.get('https://books.toscrape.com')
    element = wait_for_element(driver, 'article.product_pod')
    assert element is not None
 
 
# ── TEST 4 : extraction de liens ─────────────────────────────────
def test_extract_links(driver):
    """Vérifie que des liens sont extraits de la page."""
    driver.get('https://books.toscrape.com')
    wait_for_element(driver, 'article.product_pod')
    links = extract_links(driver)
    assert len(links) > 0
 
 
# ── TEST 5 : extraction de texte par sélecteur ───────────────────
def test_extract_text(driver):
    """Vérifie l'extraction de texte via sélecteur CSS."""
    driver.get('https://books.toscrape.com')
    wait_for_element(driver, 'h1')
    text = extract_text_by_selector(driver, 'h1')
    assert text != ''
 
 
# ── TEST 6 : pagination ──────────────────────────────────────────
def test_pagination(driver):
    """Vérifie que le bouton Suivant est trouvé et cliquable."""
    driver.get('https://books.toscrape.com')
    wait_for_element(driver, 'li.next')
    result = click_next_button(driver, next_selector='li.next a')
    assert result is True
 
 
# ── TEST 7 : élément inexistant retourne None ────────────────────
def test_element_not_found(driver):
    """Vérifie que wait_for_element retourne None si élément absent."""
    driver.get('https://books.toscrape.com')
    result = wait_for_element(driver, '#element-qui-nexiste-pas', timeout=3)
    assert result is None
