"""
Module ragas_compat.py.
"""
import os
os.environ["GIT_PYTHON_REFRESH"] = "quiet"  # évite une erreur GitPython non bloquante pour notre usage

import sys
import types
from langchain_google_vertexai import ChatVertexAI

_fake_module = types.ModuleType("langchain_community.chat_models.vertexai")
_fake_module.ChatVertexAI = ChatVertexAI
sys.modules["langchain_community.chat_models.vertexai"] = _fake_module