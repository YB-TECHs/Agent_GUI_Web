# src/selenium_layer/extractor.py
 
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from typing import Optional
import logging
 
logger = logging.getLogger(__name__)
 
 
def get_page_source(driver: webdriver.Chrome) -> str:
    """Retourne le HTML complet de la page courante."""
    return driver.page_source
 
 
def extract_table(driver: webdriver.Chrome,
                  table_index: int = 0) -> Optional[pd.DataFrame]:
    """
    Extrait un tableau HTML et le retourne comme DataFrame Pandas.
    
    Args:
        driver: Le driver Chrome
        table_index: Index du tableau à extraire (0 = premier tableau)
    Returns:
        DataFrame avec les données, ou None si aucun tableau trouvé
    """
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table')
    
    if not tables:
        logger.warning("Aucun tableau <table> trouvé dans la page.")
        return None
    
    if table_index >= len(tables):
        logger.warning(f"Index {table_index} invalide — {len(tables)} tableau(x) trouvé(s).")
        return None
    
    table = tables[table_index]
    rows = []
    headers = []
    
    # Extraire les en-têtes (<th>)
    header_row = table.find('tr')
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Extraire les lignes de données (<tr> avec <td>)
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if cells:
            rows.append([cell.get_text(strip=True) for cell in cells])
    
    if not rows:
        logger.warning("Tableau trouvé mais aucune ligne de données.")
        return None
    
    # Créer le DataFrame
    df = pd.DataFrame(rows, columns=headers if headers else None)
    logger.info(f"Tableau extrait : {len(df)} lignes, {len(df.columns)} colonnes")
    return df
 
 
def extract_all_tables(driver: webdriver.Chrome) -> list[pd.DataFrame]:
    """Extrait TOUS les tableaux de la page et les retourne en liste."""
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    tables = soup.find_all('table')
    results = []
    for i, _ in enumerate(tables):
        df = extract_table(driver, table_index=i)
        if df is not None:
            results.append(df)
    logger.info(f"{len(results)} tableau(x) extrait(s) au total.")
    return results
 
 
def extract_links(driver: webdriver.Chrome,
                  filter_keyword: str = '') -> list[dict]:
    """
    Extrait tous les liens de la page.
    Args:
        filter_keyword: Si fourni, ne garde que les liens contenant ce mot
    Returns:
        Liste de dictionnaires {'text': ..., 'href': ...}
    """
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        if filter_keyword.lower() in href.lower() or not filter_keyword:
            links.append({'text': text, 'href': href})
    logger.info(f"{len(links)} lien(s) extrait(s).")
    return links
 
 
def extract_text_by_selector(driver: webdriver.Chrome,
                             css_selector: str) -> str:
    """Extrait le texte d'un élément via son sélecteur CSS."""
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    element = soup.select_one(css_selector)
    if element:
        return element.get_text(strip=True)
    return ""
