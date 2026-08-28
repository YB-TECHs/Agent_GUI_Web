"""
Module ragas_llm_factory.py.
"""

import os
from typing import Any, List, Optional, Iterator, AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGenerationChunk, ChatGeneration
from ragas.llms import LangchainLLMWrapper


GEMINI_MODEL = "gemini-flash-latest"
GROQ_MODEL   = "qwen/qwen3.8-27b"   # Modele disponible sur ce compte Groq

RATE_LIMIT_KEYWORDS = ("429", "resource_exhausted", "rate_limit", "ratelimit", "quota", "too many")


def _est_erreur_quota(e: Exception) -> bool:
    """Detecte une erreur de quota/rate-limit."""
    msg = str(e).lower()
    return any(k in msg for k in RATE_LIMIT_KEYWORDS)


class FallbackChatModel(BaseChatModel):
    """BaseChatModel avec fallback automatique Gemini -> Groq.

    RAGAS accede directement au champ temperature sur le modele.
    Cette classe l expose correctement tout en gerant le basculement.
    """

    primary_llm: Any
    fallback_llm: Any
    temperature: float = 0.0
    n: int = 1  # RAGAS lit aussi ce champ sur certaines versions

    model_config = {"arbitrary_types_allowed": True}

    def _set_using_fallback(self, value: bool) -> None:
        """Contourne la validation Pydantic pour modifier l etat interne."""
        object.__setattr__(self, "_using_fallback", value)

    def _get_using_fallback(self) -> bool:
        return getattr(self, "_using_fallback", False)

    @property
    def _llm_type(self) -> str:
        return "gemini_groq_fallback"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs,
    ) -> ChatResult:
        if not self._get_using_fallback():
            try:
                return self.primary_llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            except Exception as e:
                if _est_erreur_quota(e):
                    print("\n[FALLBACK] Quota Gemini epuise -> basculement automatique sur Groq")
                    self._set_using_fallback(True)
                else:
                    raise
        return self.fallback_llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs,
    ) -> ChatResult:
        if not self._get_using_fallback():
            try:
                return await self.primary_llm._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
            except Exception as e:
                if _est_erreur_quota(e):
                    print("\n[FALLBACK] Quota Gemini epuise -> basculement automatique sur Groq")
                    self._set_using_fallback(True)
                else:
                    raise
        return await self.fallback_llm._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)


def creer_llm_ragas(verbose: bool = True) -> LangchainLLMWrapper:
    """Retourne un LangchainLLMWrapper Gemini+Groq avec fallback automatique.

    Args:
        verbose: Affiche les providers disponibles.

    Returns:
        LangchainLLMWrapper pret pour ragas.evaluate().
    """
    google_key = os.environ.get("GOOGLE_API_KEY", "")
    groq_key   = os.environ.get("GROQ_API_KEY", "")

    if not google_key and not groq_key:
        raise EnvironmentError(
            "Aucune cle API disponible.\n"
            "Definir au moins une variable :\n"
            "  $env:GOOGLE_API_KEY='AIza...'\n"
            "  $env:GROQ_API_KEY='gsk_...'"
        )

    gemini, groq = None, None

    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL, google_api_key=google_key, temperature=0
            )
            if verbose:
                print(f"  [LLM] Provider 1 : Gemini ({GEMINI_MODEL})")
        except ImportError:
            if verbose:
                print("  [LLM] langchain-google-genai absent, Gemini ignore.")

    if groq_key:
        try:
            from langchain_groq import ChatGroq
            groq = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0)
            if verbose:
                print(f"  [LLM] Provider 2 : Groq ({GROQ_MODEL}) -- fallback si quota Gemini epuise")
        except ImportError:
            if verbose:
                print("  [LLM] langchain-groq absent, Groq ignore.")

    if gemini and groq:
        if verbose:
            print(f"  [LLM] Mode : fallback automatique Gemini -> Groq\n")
        model = FallbackChatModel(primary_llm=gemini, fallback_llm=groq)
        return LangchainLLMWrapper(model)

    if gemini:
        if verbose:
            print(f"  [LLM] Mode : Gemini seul (pas de cle Groq)\n")
        return LangchainLLMWrapper(gemini)

    if groq:
        if verbose:
            print(f"  [LLM] Mode : Groq seul (pas de cle Gemini)\n")
        return LangchainLLMWrapper(groq)

    raise EnvironmentError("Aucun provider LLM disponible.")
