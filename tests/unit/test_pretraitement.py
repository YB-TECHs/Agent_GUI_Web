"""
Module test_pretraitement.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rag_agent import pretraitement_bm25, supprimer_accents, MOTS_VIDES_FRANCAIS


class TestSupprimerAccents:
    """Tests de la fonction supprimer_accents (normalisation Unicode)."""

    def test_accent_aigu(self):
        assert supprimer_accents("épargne") == "epargne"

    def test_accent_grave(self):
        assert supprimer_accents("système") == "systeme"

    def test_ville_yaounde(self):
        # Cas reel ayant cause un bug (rang BM25 265 au lieu de 8)
        assert supprimer_accents("Yaoundé") == "Yaounde"

    def test_sans_accent_inchange(self):
        assert supprimer_accents("Maroua") == "Maroua"

    def test_chaine_vide(self):
        assert supprimer_accents("") == ""

    def test_cedille(self):
        assert supprimer_accents("garçon") == "garcon"


class TestPretraitementBM25:
    """Tests de la tokenisation BM25 (minuscule + sans accent + sans stopword)."""

    def test_mise_en_minuscule(self):
        tokens = pretraitement_bm25("MAROUA")
        assert "maroua" in tokens

    def test_insensibilite_casse_maroua(self):
        # fix : "maroua" (question) ne matchait pas "Maroua" (document)
        assert pretraitement_bm25("maroua") == pretraitement_bm25("Maroua")

    def test_insensibilite_accent_yaounde(self):
        # fix : "Yaounde" (sans accent) ne matchait pas "Yaoundé"
        assert pretraitement_bm25("Yaounde") == pretraitement_bm25("Yaoundé")

    def test_retrait_mots_vides(self):
        tokens = pretraitement_bm25("quelles sont les microfinances presentes a maroua")
        for mot_vide in ("quelles", "sont", "les", "a"):
            assert mot_vide not in tokens
        assert "microfinances" in tokens
        assert "maroua" in tokens

    def test_mot_rare_conserve(self):
        tokens = pretraitement_bm25("Qu'est-ce que CamCCUL ?")
        assert "camccul" in tokens

    def test_chaine_vide(self):
        assert pretraitement_bm25("") == []


class TestMotsVidesFrancais:
    """Verifie que la liste de mots vides est coherente."""

    def test_contient_articles_courants(self):
        for mot in ("le", "la", "les", "un", "une", "des"):
            assert mot in MOTS_VIDES_FRANCAIS

    def test_ne_contient_pas_mots_significatifs(self):
        for mot in ("microfinance", "maroua", "cobac", "credit"):
            assert mot not in MOTS_VIDES_FRANCAIS