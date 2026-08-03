"""
Outil de RECHERCHE EXHAUSTIVE par ville — complementaire a l'agent RAG.

Contrairement a rag_agent.py (qui repond via un LLM a partir d'un nombre
LIMITE de chunks, adapte aux questions ponctuelles mais pas a
l'enumeration complete), cet outil affiche TOUS les chunks du corpus
contenant litteralement le nom d'une ville donnee, sans passer par le
LLM. Aucune limite de nombre de resultats, aucun risque d'oubli ou
d'invention : c'est une recherche brute, exhaustive et fiable.

IMPORTANT : distingue les mentions de VILLE (localisation d'un
etablissement) des cas ou le meme mot apparaitrait comme nom propre
d'un dirigeant (ex. un nom de famille camerounais identique a un nom de
ville). La distinction se fait ligne par ligne : si la ligne contenant
le mot recherche contient AUSSI une etiquette de dirigeant (PCA, DG,
DGA, CAC), l'occurrence est consideree comme un possible nom propre et
signalee separement plutot que comptee comme une vraie localisation.

Usage :
    python src/recherche_exhaustive_ville.py Douala
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag_agent import charger_tous_les_chunks, supprimer_accents

MOTIF_ETIQUETTE_DIRIGEANT = re.compile(r"\b(PCA|DG|DGA|CAC)\b\s*[:.]", re.IGNORECASE)


def ligne_est_probablement_un_nom_propre(ligne):
    """Retourne True si la ligne contient une etiquette de dirigeant
    (PCA/DG/DGA/CAC), suggerant que le mot recherche y apparait comme
    nom propre plutot que comme localisation."""
    return bool(MOTIF_ETIQUETTE_DIRIGEANT.search(ligne))


def analyser_chunk(page_content, ville_normalisee):
    """Decoupe le chunk en lignes et classe chaque ligne contenant la
    ville en 'localisation probable' ou 'nom propre probable'."""
    lignes_localisation = []
    lignes_nom_propre = []

    for ligne in page_content.splitlines():
        ligne_normalisee = supprimer_accents(ligne.lower())
        motif = r"\b" + re.escape(ville_normalisee) + r"\b"
        if re.search(motif, ligne_normalisee):
            if ligne_est_probablement_un_nom_propre(ligne):
                lignes_nom_propre.append(ligne.strip())
            else:
                lignes_localisation.append(ligne.strip())

    return lignes_localisation, lignes_nom_propre


def main():
    if len(sys.argv) != 2:
        print("Usage : python src/recherche_exhaustive_ville.py NomDeLaVille")
        sys.exit(1)

    ville = sys.argv[1]
    ville_normalisee = supprimer_accents(ville.lower())

    print("Chargement de l'index (recherche exhaustive, pas de limite)...")
    _, tous_les_documents = charger_tous_les_chunks()

    chunks_avec_localisation = []
    chunks_avec_nom_propre_uniquement = []

    for doc in tous_les_documents:
        contenu_normalise = supprimer_accents(doc.page_content.lower())
        motif = r"\b" + re.escape(ville_normalisee) + r"\b"
        if not re.search(motif, contenu_normalise):
            continue

        lignes_localisation, lignes_nom_propre = analyser_chunk(doc.page_content, ville_normalisee)

        if lignes_localisation:
            chunks_avec_localisation.append((doc, lignes_localisation))
        elif lignes_nom_propre:
            chunks_avec_nom_propre_uniquement.append((doc, lignes_nom_propre))

    print(f"\n{'='*70}")
    print(f"RECHERCHE EXHAUSTIVE : '{ville}'")
    print(f"{'='*70}")
    print(f"{len(chunks_avec_localisation)} chunk(s) avec '{ville}' comme LOCALISATION probable")
    print(f"{len(chunks_avec_nom_propre_uniquement)} chunk(s) ecarte(s) car '{ville}' y apparait "
          f"uniquement pres d'une etiquette de dirigeant (PCA/DG/DGA/CAC) — probablement un nom propre\n")

    print(f"{'='*70}")
    print("CHUNKS RETENUS (localisation probable) :")
    print(f"{'='*70}\n")
    for i, (doc, lignes) in enumerate(chunks_avec_localisation, start=1):
        print(f"--- Chunk {i}/{len(chunks_avec_localisation)} ---")
        print(f"Ligne(s) de localisation detectee(s) : {lignes}")
        print(doc.page_content.strip())
        print()

    if chunks_avec_nom_propre_uniquement:
        print(f"{'='*70}")
        print("CHUNKS ECARTES (probable nom propre, pas une localisation) :")
        print(f"{'='*70}\n")
        for i, (doc, lignes) in enumerate(chunks_avec_nom_propre_uniquement, start=1):
            print(f"--- Chunk ecarte {i}/{len(chunks_avec_nom_propre_uniquement)} ---")
            print(f"Ligne(s) suspecte(s) (nom propre) : {lignes}")
            print(doc.page_content[:200].strip())
            print()

    if not chunks_avec_localisation and not chunks_avec_nom_propre_uniquement:
        print("Aucun chunk ne mentionne cette ville. Verifie l'orthographe, "
              "ou il se peut que cette ville ne soit simplement pas couverte "
              "par le corpus.")
    else:
        print(f"{'='*70}")
        print("IMPORTANT : ce texte brut peut etre fragmente (extraction PDF "
              "de tableau). La distinction localisation/nom propre est une "
              "heuristique (basee sur la presence d'etiquettes PCA/DG/DGA/CAC "
              "sur la meme ligne) — verifie visuellement en cas de doute.")


if __name__ == "__main__":
    main()