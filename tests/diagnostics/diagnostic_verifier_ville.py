"""
Module diagnostic_verifier_ville.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rag_agent import charger_tous_les_chunks

# Modifie ce mot pour tester une autre ville
MOT_A_CHERCHER = "Yaound"


def main():
    print("Chargement des chunks...")
    _, tous_les_documents = charger_tous_les_chunks()

    trouves = [d for d in tous_les_documents if MOT_A_CHERCHER in d.page_content]
    print(f"\nNombre de chunks contenant '{MOT_A_CHERCHER}' : {len(trouves)}")

    for i, doc in enumerate(trouves[:5]):
        print(f"\n--- Chunk {i+1} ---")
        print(doc.page_content[:400])


if __name__ == "__main__":
    main()
