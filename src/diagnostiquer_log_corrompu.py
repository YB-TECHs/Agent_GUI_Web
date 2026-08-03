"""
Diagnostic PRECIS du journal maitre corrompu (interactions_log.csv).

Contrairement a pandas (qui peut se tromper sur des champs contenant des
retours a la ligne integres), ce script utilise le module csv standard
de Python, qui respecte correctement les guillemets et les retours a la
ligne a l'interieur d'un champ cite. Il isole les VRAIES lignes
malformees (nombre de colonnes incorrect) et affiche leur contenu brut
exact, pour comprendre la cause reelle avant toute correction.

Usage :
    python src/diagnostiquer_log_corrompu.py
"""

import csv
from pathlib import Path

FICHIER_LOG = Path("data/processed/interactions_log.csv")


def main():
    with open(FICHIER_LOG, newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        entete = next(lecteur)
        print(f"En-tete detecte ({len(entete)} colonnes) : {entete}\n")

        lignes_bonnes = 0
        lignes_mauvaises = []

        for numero_ligne, ligne in enumerate(lecteur, start=2):
            if len(ligne) == len(entete):
                lignes_bonnes += 1
            else:
                lignes_mauvaises.append((numero_ligne, ligne))

    print(f"Lignes correctement formees : {lignes_bonnes}")
    print(f"Lignes malformees : {len(lignes_mauvaises)}\n")

    if lignes_mauvaises:
        print("=" * 70)
        print("DETAIL DES PREMIERES LIGNES MALFORMEES (contenu brut exact)")
        print("=" * 70)
        for numero_ligne, ligne in lignes_mauvaises[:10]:
            print(f"\n--- Ligne logique n{numero_ligne} ({len(ligne)} champs "
                  f"au lieu de {len(entete)}) ---")
            for i, champ in enumerate(ligne):
                apercu = champ[:150].replace("\n", "\\n")
                print(f"  Champ {i}: {apercu!r}")
    else:
        print("Aucune ligne malformee detectee par le module csv standard : "
              "le fichier est en realite valide. Le probleme rencontre "
              "avec pandas provient donc d'autre chose (a investiguer).")


if __name__ == "__main__":
    main()
