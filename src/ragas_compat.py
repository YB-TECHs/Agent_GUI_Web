"""
Correctif de compatibilité pour ragas 0.3.9 avec langchain-community récent.
Bug connu : ragas/llms/base.py importe langchain_community.chat_models.vertexai,
un chemin supprimé dans les versions récentes de langchain-community.
Ce shim redirige l'import vers langchain_google_vertexai sans modifier
les fichiers installés (donc reproductible et robuste aux réinstallations).
Doit être importé AVANT tout import de `ragas`.
"""
import os
os.environ["GIT_PYTHON_REFRESH"] = "quiet"  # évite une erreur GitPython non bloquante pour notre usage

import sys
import types
from langchain_google_vertexai import ChatVertexAI

_fake_module = types.ModuleType("langchain_community.chat_models.vertexai")
_fake_module.ChatVertexAI = ChatVertexAI
sys.modules["langchain_community.chat_models.vertexai"] = _fake_module