# src/orchestrator_layer/memoire_conversation.py
from collections import deque

MAX_MESSAGES = 100
_historique = deque(maxlen=MAX_MESSAGES)


def ajouter_message(role: str, contenu: str) -> None:
    """role : 'user' ou 'assistant'."""
    _historique.append({'role': role, 'content': contenu})


def obtenir_historique() -> list[dict]:
    return list(_historique)


def reinitialiser() -> None:
    _historique.clear()