"""
Module reparer_log_maitre.py.
"""

import csv
import shutil
from pathlib import Path

FICHIER_LOG = Path("data/processed/interactions_log.csv")
FICHIER_SAUVEGARDE = Path("data/processed/interactions_log_avant_reparation.csv")

ANCIEN_ENTETE = [
    "timestamp", "question", "reponse", "nb_documents_recuperes",
    "extrait_contexte", "temps_reponse_secondes", "statut",
]
NOUVEL_ENTETE = [
    "timestamp", "question", "reponse", "nb_documents_recuperes",
    "score_similarite", "extrait_contexte", "temps_reponse_secondes", "statut",
]

POSITION_SCORE_SIMILARITE = 4  # entre nb_documents_recuperes et extrait_contexte


def main():
    if not FICHIER_LOG.exists():
        print(f"Fichier introuvable : {FICHIER_LOG}. Rien a reparer.")
        return

    shutil.copy2(FICHIER_LOG, FICHIER_SAUVEGARDE)
    print(f"Sauvegarde de l'original creee : {FICHIER_SAUVEGARDE}")

    with open(FICHIER_LOG, newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        entete_actuel = next(lecteur)
        toutes_les_lignes = list(lecteur)

    lignes_reparees = []
    nb_anciennes = 0
    nb_deja_bonnes = 0
    nb_vraiment_anormales = 0

    for numero, ligne in enumerate(toutes_les_lignes, start=2):
        if len(ligne) == len(ANCIEN_ENTETE):
            # Ancienne ligne (avant l'ajout de score_similarite) : on
            # insere une valeur vide a la bonne position, sans rien
            # inventer.
            ligne_reparee = (
                ligne[:POSITION_SCORE_SIMILARITE]
                + [""]
                + ligne[POSITION_SCORE_SIMILARITE:]
            )
            lignes_reparees.append(ligne_reparee)
            nb_anciennes += 1
        elif len(ligne) == len(NOUVEL_ENTETE):
            lignes_reparees.append(ligne)
            nb_deja_bonnes += 1
        else:
            print(f"  /!\\ Ligne {numero} vraiment anormale ({len(ligne)} champs), "
                  f"conservee telle quelle pour verification manuelle : {ligne}")
            lignes_reparees.append(ligne)
            nb_vraiment_anormales += 1

    with open(FICHIER_LOG, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        ecrivain.writerow(NOUVEL_ENTETE)
        ecrivain.writerows(lignes_reparees)

    print(f"\n{'='*60}")
    print("REPARATION TERMINEE")
    print(f"{'='*60}")
    print(f"Lignes anciennes (7 champs) migrees vers le schema a 8 colonnes : {nb_anciennes}")
    print(f"Lignes deja au bon format (8 champs) : {nb_deja_bonnes}")
    print(f"Lignes vraiment anormales (ni 7 ni 8 champs) : {nb_vraiment_anormales}")
    print(f"Total de lignes dans le fichier repare : {len(lignes_reparees)}")
    print(f"\nAucune donnee n'a ete perdue. L'original est conserve dans : {FICHIER_SAUVEGARDE}")

    if nb_vraiment_anormales > 0:
        print(f"\n/!\\ {nb_vraiment_anormales} ligne(s) necessitent une verification manuelle "
              f"(affichees ci-dessus).")


if __name__ == "__main__":
    main()
