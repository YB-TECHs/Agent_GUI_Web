"""
Module ollama_ragas.py.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Any, Dict

from langchain_core.outputs import Generation, LLMResult
from ragas.llms.base import BaseRagasLLM
import requests

if TYPE_CHECKING:
    from langchain_core.callbacks import Callbacks
    from langchain_core.prompt_values import PromptValue


@dataclass
class OllamaJsonRagasLLM(BaseRagasLLM):
    """Adaptateur LLM local pour RAGAS - avec nettoyage robuste du JSON."""

    model: str = "llama3.2:3b"
    base_url: str = "http://127.0.0.1:11434"
    timeout: int = 600
    max_tokens: int = 1024
    num_ctx: int = 8192
    temperature: float = 0.01
    _api_url: str = field(init=False, repr=False)

    def __post_init__(self):
        super().__post_init__()
        self._api_url = f"{self.base_url.rstrip('/')}/api/generate"

    def _call_ollama(self, prompt: str) -> str:
        """Appelle Ollama et retourne la réponse brute."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.01,
            "keep_alive": "30m",
            "options": {
                "num_ctx": self.num_ctx,
                "num_predict": self.max_tokens,
            },
        }
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["response"]

    def _extraire_json(self, text: str):
        """Extrait le premier objet JSON valide dans text en utilisant une
        approche par pile de profondeur (gere les guillemets, les echappements,
        et le texte prefixe comme 'La reponse est: {...)').

        Retourne l'objet Python parse, ou None si aucun JSON valide trouve.
        """
        start = text.find("{")
        while start != -1:
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start, len(text)):
                c = text[i]
                if escape_next:
                    escape_next = False
                    continue
                if c == "\\" and in_string:
                    escape_next = True
                    continue
                if c == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start: i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            # Ce debut de { n'etait pas valide, chercher le suivant
                            break
            start = text.find("{", start + 1)
        return None

    def _force_json(self, text: str) -> str:
        """Transforme n'importe quelle reponse en JSON valide.

        Strategie :
        1. Parsing direct (reponse deja bien formee).
        2. Extraction par pile — gere le texte prefixe avant le JSON.
        3. Dernier recours : encapsuler le texte brut dans {"text": "..."}.
        """
        text = text.strip()

        # 1. Parsing direct
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        # 2. Extraction par pile
        parsed = self._extraire_json(text)
        if parsed is not None:
            return json.dumps(parsed, ensure_ascii=False)

        # 3. Dernier recours
        return json.dumps({"text": text[:500]}, ensure_ascii=False)

    def _generate_one(self, prompt: str, temperature: float) -> Generation:
        """Génère une réponse et force le format JSON."""
        try:
            # Ajouter instruction explicite
            full_prompt = prompt + "\n\nRéponds UNIQUEMENT avec un objet JSON valide. Ne mets aucun texte avant ou après."
            
            response = self._call_ollama(full_prompt)
            
            # Nettoyer et forcer le JSON
            cleaned = self._force_json(response)
            
            return Generation(text=cleaned)
            
        except Exception as e:
            return Generation(text=json.dumps({"error": str(e)}, ensure_ascii=False))

    def generate_text(
        self,
        prompt: "PromptValue",
        n: int = 1,
        temperature: float = 0.01,
        stop: Optional[list[str]] = None,
        callbacks: "Callbacks" = None,
    ) -> LLMResult:
        generations = [
            self._generate_one(prompt.to_string(), temperature)
            for _ in range(n)
        ]
        return LLMResult(generations=[generations])

    async def agenerate_text(
        self,
        prompt: "PromptValue",
        n: int = 1,
        temperature: Optional[float] = 0.01,
        stop: Optional[list[str]] = None,
        callbacks: "Callbacks" = None,
    ) -> LLMResult:
        resolved_temperature = 0.01 if temperature is None else temperature
        generations = []
        for _ in range(n):
            generation = await asyncio.to_thread(
                self._generate_one,
                prompt.to_string(),
                resolved_temperature,
            )
            generations.append(generation)
        return LLMResult(generations=[generations])

    def is_finished(self, response: LLMResult) -> bool:
        return all(generation.text.strip() for generation in response.generations[0])