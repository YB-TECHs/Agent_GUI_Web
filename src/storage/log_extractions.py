# src/storage/log_extractions.py
import sqlite3
from datetime import datetime
from pathlib import Path

CHEMIN_LOG = 'data/processed/log_extractions.db'


def _connexion() -> sqlite3.Connection:
    Path(CHEMIN_LOG).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CHEMIN_LOG)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            url TEXT,
            question TEXT,
            source TEXT,
            erreur_llm INTEGER,
            statut TEXT,
            duree_secondes REAL,
            reponse_finale TEXT
        )
    ''')
    return conn


def enregistrer_extraction(url: str, question: str, source: str, erreur_llm: bool,
                            duree_secondes: float, reponse_finale: str | None = None,
                            statut: str = 'succes') -> None:
    """Ajoute une ligne au log. Ne lève jamais d'exception vers l'appelant :
    un souci de journalisation ne doit jamais faire échouer une extraction."""
    try:
        conn = _connexion()
        conn.execute(
            'INSERT INTO extractions (timestamp, url, question, source, erreur_llm, '
            'statut, duree_secondes, reponse_finale) VALUES (?,?,?,?,?,?,?,?)',
            (datetime.now().isoformat(), url, question, source, int(erreur_llm),
             statut, duree_secondes, (reponse_finale or '')[:300]),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # la journalisation est un bonus, pas un prérequis de fonctionnement


def lire_extractions(limite: int = 200) -> list[dict]:
    conn = _connexion()
    conn.row_factory = sqlite3.Row
    lignes = conn.execute(
        'SELECT * FROM extractions ORDER BY id DESC LIMIT ?', (limite,)
    ).fetchall()
    conn.close()
    return [dict(l) for l in lignes]


def statistiques() -> dict:
    conn = _connexion()
    total = conn.execute('SELECT COUNT(*) FROM extractions').fetchone()[0]
    par_source = dict(conn.execute(
        'SELECT source, COUNT(*) FROM extractions GROUP BY source'
    ).fetchall())
    taux_erreur = conn.execute('SELECT AVG(erreur_llm) FROM extractions').fetchone()[0] or 0
    duree_discussion = conn.execute(
        "SELECT AVG(duree_secondes) FROM extractions WHERE source = 'discussion'"
    ).fetchone()[0] or 0
    duree_extraction = conn.execute(
        "SELECT AVG(duree_secondes) FROM extractions WHERE source != 'discussion'"
    ).fetchone()[0] or 0
    conn.close()
    return {
        'total': total,
        'par_source': par_source,
        'taux_erreur_llm': round(taux_erreur, 3),
        'duree_moyenne_discussion_secondes': round(duree_discussion, 2),
        'duree_moyenne_extraction_secondes': round(duree_extraction, 2),
    }