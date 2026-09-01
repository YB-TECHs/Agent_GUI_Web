# src/orchestrator_layer/memoire_conversation.py
import json
from collections import deque
from pathlib import Path

MAX_MESSAGES = 100
CHEMIN_MEMOIRE = Path('data/processed/memoire_conversation.json')


def _charger() -> deque:
    if CHEMIN_MEMOIRE.exists():
        try:
            donnees = json.loads(CHEMIN_MEMOIRE.read_text(encoding='utf-8'))
            return deque(donnees, maxlen=MAX_MESSAGES)
        except Exception:
            pass  # fichier corrompu ou illisible → on repart d'un historique vide
    return deque(maxlen=MAX_MESSAGES)


_historique = _charger()


def _sauvegarder() -> None:
    try:
        CHEMIN_MEMOIRE.parent.mkdir(parents=True, exist_ok=True)
        CHEMIN_MEMOIRE.write_text(
            json.dumps(list(_historique), ensure_ascii=False, indent=2), encoding='utf-8'
        )
    except Exception:
        pass  # la persistance est un bonus, pas un prérequis de fonctionnement


def ajouter_message(role: str, contenu: str) -> None:
    _historique.append({'role': role, 'content': contenu})
    _sauvegarder()


def obtenir_historique() -> list[dict]:
    return list(_historique)


def reinitialiser() -> None:
    _historique.clear()
    _sauvegarder()