"""
Nettoyage et structuration du jeu de donnees d'interactions (S2 + S3).

Conforme a la section 4 du cahier des charges :
    - Deduplication des enregistrements strictement identiques
    - Typage explicite des champs (dates, scores numeriques, chaines,
      booleens de succes/echec)
    - Validation par regles metier configurables (score de similarite
      entre 0 et 1, temps de reponse positif)
    - Structuration finale en DataFrame exportable (CSV/JSON/SQLite),
      accompagne d'un dictionnaire de donnees

Usage :
    python src/nettoyage_dataset.py
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

FICHIER_S2 = Path("data/processed/resultats_tests_S2.csv")
FICHIER_S3 = Path("data/processed/dataset_interactions_S3.csv")
FICHIER_LOG_MAITRE = Path("data/processed/interactions_log.csv")
FICHIER_CORRECTIONS = Path("data/processed/corrections_confusion_villes.csv")

DOSSIER_SORTIE = Path("data/processed")
FICHIER_BRUT_FUSIONNE = DOSSIER_SORTIE / "dataset_brut_fusionne.csv"
FICHIER_NETTOYE_CSV = DOSSIER_SORTIE / "dataset_final_nettoye.csv"
FICHIER_NETTOYE_JSON = DOSSIER_SORTIE / "dataset_final_nettoye.json"
FICHIER_NETTOYE_SQLITE = DOSSIER_SORTIE / "dataset_final_nettoye.sqlite"
FICHIER_RAPPORT_ANOMALIES = DOSSIER_SORTIE / "rapport_anomalies_nettoyage.csv"
FICHIER_DICTIONNAIRE = Path("docs/Dictionnaire_Donnees.md")


def charger_et_fusionner():
    """Charge S2 et S3, harmonise leurs colonnes et les fusionne en un
    seul DataFrame, avec une colonne 'source' pour tracer l'origine."""
    df_s2 = pd.read_csv(FICHIER_S2, encoding="utf-8")
    df_s2["source"] = "S2"

    df_s3 = pd.read_csv(FICHIER_S3, encoding="utf-8")
    df_s3["source"] = "S3"

    # S2 a ete genere AVANT l'ajout du score de similarite au pipeline :
    # la colonne n'existe donc pas dans ce fichier. On l'ajoute
    # explicitement en valeurs manquantes plutot que de la laisser
    # absente silencieusement (transparence sur la limite du dataset).
    if "score_similarite" not in df_s2.columns:
        df_s2["score_similarite"] = pd.NA

    colonnes_communes = [
        "id", "categorie", "question", "reponse",
        "nb_documents_recuperes", "score_similarite",
        "temps_reponse_secondes", "statut", "source",
    ]
    df_s2 = df_s2[colonnes_communes]
    df_s3 = df_s3[colonnes_communes]

    df = pd.concat([df_s2, df_s3], ignore_index=True)
    return df


def appliquer_corrections_confusion_villes(df):
    """Applique, de facon TRACEE, les corrections regenerees avec l'index
    corrige (script corriger_reponses_confuses.py) suite au bug de
    decoupage region/footer decouvert dans build_index.py.

    Les fichiers bruts (S2/S3) ne sont jamais modifies : les corrections
    sont surimposees ici, sur une copie, avec une colonne booleenne
    'corrige_bug_decoupage_region' explicite pour tracer precisement
    quelles lignes ont ete affectees et pourquoi.
    """
    df["corrige_bug_decoupage_region"] = False

    if not FICHIER_CORRECTIONS.exists():
        print("Aucun fichier de corrections trouve (corrections_confusion_villes.csv) : "
              "dataset utilise tel quel, sans correction post-bugfix.")
        return df

    df_corrections = pd.read_csv(FICHIER_CORRECTIONS, encoding="utf-8")
    print(f"Application de {len(df_corrections)} correction(s) issues du bugfix "
          f"de decoupage region/footer...")

    for _, correction in df_corrections.iterrows():
        masque = df["id"] == correction["id"]
        if not masque.any():
            print(f"  /!\\ id {correction['id']} non trouve dans le dataset fusionne, ignore")
            continue

        df.loc[masque, "reponse"] = correction["nouvelle_reponse"]
        df.loc[masque, "nb_documents_recuperes"] = correction["nouveau_nb_documents"]
        df.loc[masque, "score_similarite"] = correction["nouveau_score_similarite"]
        df.loc[masque, "temps_reponse_secondes"] = correction["nouveau_temps_reponse"]
        df.loc[masque, "statut"] = correction["nouveau_statut"]
        df.loc[masque, "corrige_bug_decoupage_region"] = True

    nb_corrigees = df["corrige_bug_decoupage_region"].sum()
    print(f"{nb_corrigees} ligne(s) effectivement corrigee(s) et tracee(s) "
          f"dans la colonne 'corrige_bug_decoupage_region'.")

    return df


def enrichir_avec_timestamp(df):
    """Recupere un timestamp par question depuis le journal maitre des
    interactions (qui, lui, horodate chaque appel), pour satisfaire
    l'exigence de typage explicite des dates (section 4). Si une
    question a ete posee plusieurs fois (tests, debogage), on retient
    le DERNIER horodatage correspondant.

    Robuste aux lignes malformees du journal maitre (ex. une reponse
    contenant une virgule mal echappee suite a une ouverture/sauvegarde
    accidentelle dans un tableur) : les lignes illisibles sont ignorees
    plutot que de faire planter tout le nettoyage, et si le fichier est
    totalement illisible, on degrade proprement (timestamp absent pour
    toutes les lignes) plutot que de crasher.
    """
    if not FICHIER_LOG_MAITRE.exists():
        df["timestamp"] = pd.NaT
        return df

    try:
        df_log = pd.read_csv(
            FICHIER_LOG_MAITRE,
            encoding="utf-8",
            engine="python",
            on_bad_lines="warn",
        )
    except Exception as e:
        print(f"/!\\ Journal maitre illisible ({e}). "
              f"Colonne timestamp laissee vide pour tout le dataset.")
        df["timestamp"] = pd.NaT
        return df

    if "timestamp" not in df_log.columns or "question" not in df_log.columns:
        print("/!\\ Colonnes 'timestamp'/'question' absentes du journal maitre. "
              "Colonne timestamp laissee vide.")
        df["timestamp"] = pd.NaT
        return df

    dernier_timestamp_par_question = (
        df_log.sort_values("timestamp")
        .drop_duplicates(subset="question", keep="last")
        .set_index("question")["timestamp"]
    )

    df["timestamp"] = df["question"].map(dernier_timestamp_par_question)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def dedupliquer(df):
    """Supprime les enregistrements STRICTEMENT identiques (toutes
    colonnes egales), comme demande section 4. Ne supprime pas les
    questions reformulees ou posees a des moments differents."""
    avant = len(df)
    df = df.drop_duplicates(
        subset=["question", "reponse", "temps_reponse_secondes", "statut"],
        keep="first",
    )
    apres = len(df)
    print(f"Deduplication : {avant - apres} doublon(s) strict(s) retire(s) ({avant} -> {apres})")
    return df


def typer_les_champs(df):
    """Typage explicite de chaque champ, y compris un booleen de
    succes/echec derive du champ 'statut' texte (exigence section 4)."""
    df["id"] = df["id"].astype("string")
    df["categorie"] = df["categorie"].astype("category")
    df["question"] = df["question"].astype("string")
    df["reponse"] = df["reponse"].astype("string")
    df["source"] = df["source"].astype("category")
    df["statut"] = df["statut"].astype("string")

    df["nb_documents_recuperes"] = pd.to_numeric(
        df["nb_documents_recuperes"], errors="coerce"
    ).astype("Int64")
    df["score_similarite"] = pd.to_numeric(df["score_similarite"], errors="coerce")
    df["temps_reponse_secondes"] = pd.to_numeric(
        df["temps_reponse_secondes"], errors="coerce"
    )

    # Booleen de succes/echec explicitement demande section 4.
    df["succes"] = df["statut"].str.lower().eq("succes")

    return df


def valider_regles_metier(df):
    """Applique les regles de validation de la section 4 :
    - score de similarite entre 0 et 1 (quand renseigne)
    - temps de reponse strictement positif
    - nombre de documents recuperes non negatif

    Ne supprime PAS silencieusement les lignes invalides : les marque
    et produit un rapport separe, pour rester transparent sur les
    anomalies plutot que de les cacher.
    """
    score_valide = df["score_similarite"].isna() | df["score_similarite"].between(0, 1)
    temps_valide = df["temps_reponse_secondes"] > 0
    nb_docs_valide = df["nb_documents_recuperes"] >= 0

    df["valide"] = score_valide & temps_valide & nb_docs_valide

    anomalies = df[~df["valide"]].copy()
    if len(anomalies) > 0:
        anomalies["raison_anomalie"] = ""
        anomalies.loc[~score_valide[~df["valide"]], "raison_anomalie"] += "score_hors_bornes;"
        anomalies.loc[~temps_valide[~df["valide"]], "raison_anomalie"] += "temps_reponse_invalide;"
        anomalies.loc[~nb_docs_valide[~df["valide"]], "raison_anomalie"] += "nb_documents_invalide;"
        anomalies.to_csv(FICHIER_RAPPORT_ANOMALIES, index=False, encoding="utf-8-sig")
        print(f"/!\\ {len(anomalies)} anomalie(s) detectee(s), rapport dans : {FICHIER_RAPPORT_ANOMALIES}")
    else:
        print("Aucune anomalie detectee : toutes les regles metier sont respectees.")

    return df


def generer_dictionnaire_donnees(df):
    """Genere un dictionnaire de donnees markdown decrivant chaque
    colonne du dataset final (exigence section 4)."""
    descriptions = {
        "id": "Identifiant unique de l'interaction (ex. Q01, S3-042).",
        "categorie": "Categorie de la question (definitions, reglementation, "
                     "categories_emf, institutions, geo_tabulaire, scenario, "
                     "comparaison, chiffres, ambigue, hors_perimetre).",
        "question": "Texte de la question posee a l'agent RAG.",
        "reponse": "Texte de la reponse generee par le LLM.",
        "nb_documents_recuperes": "Nombre de chunks retournes par le retriever "
                                  "hybride (BM25+FAISS) apres fusion, borne par "
                                  "MAX_CONTEXTE_CHUNKS.",
        "score_similarite": "Score de similarite semantique du meilleur chunk "
                             "FAISS, normalise entre 0 et 1 via 1/(1+distance_L2). "
                             "ABSENT pour les interactions S2 (colonne ajoutee "
                             "apres la campagne de tests S2) : valeurs manquantes "
                             "(NaN) pour ces lignes, non imputees.",
        "temps_reponse_secondes": "Temps total de traitement de la question, "
                                  "en secondes (recuperation + generation LLM).",
        "statut": "Statut brut de l'execution : 'succes' ou 'echec' (erreur "
                  "technique lors du traitement).",
        "source": "Semaine de generation de l'interaction : S2 (campagne de "
                  "validation initiale, 35 questions) ou S3 (generation "
                  "massive du dataset, 275 questions).",
        "timestamp": "Date et heure de l'interaction, recuperee depuis le "
                     "journal maitre (data/processed/interactions_log.csv) par "
                     "correspondance sur le texte de la question. Absent (NaT) "
                     "si aucune correspondance trouvee.",
        "succes": "Booleen derive de 'statut' : True si statut == 'succes', "
                  "False sinon.",
        "valide": "Booleen issu de la validation par regles metier (section 4) "
                  ": True si score_similarite dans [0,1] (ou absent), "
                  "temps_reponse_secondes > 0, et nb_documents_recuperes >= 0.",
        "corrige_bug_decoupage_region": "Booleen : True si cette ligne a ete "
                  "regeneree avec l'index corrige suite a la decouverte d'un "
                  "bug de decoupage (chunks a cheval sur deux regions, ou "
                  "pollues par un encart publicitaire). Concerne les cas de "
                  "confusion de ville identifies par verifier_confusion_villes.py "
                  "puis corriges par corriger_reponses_confuses.py.",
    }

    lignes = [
        "# Dictionnaire de donnees — Dataset d'interactions RAG (S2 + S3)",
        "",
        f"Genere automatiquement par `src/nettoyage_dataset.py`.",
        f"Nombre total d'enregistrements : {len(df)}",
        "",
        "| Colonne | Type Pandas | Description |",
        "|---|---|---|",
    ]
    for colonne in df.columns:
        type_pandas = str(df[colonne].dtype)
        description = descriptions.get(colonne, "(description non renseignee)")
        lignes.append(f"| `{colonne}` | `{type_pandas}` | {description} |")

    lignes += [
        "",
        "## Statistiques rapides",
        "",
        f"- Repartition par source : {df['source'].value_counts().to_dict()}",
        f"- Repartition par categorie : {df['categorie'].value_counts().to_dict()}",
        f"- Taux de succes global : {df['succes'].mean():.1%}",
        f"- Lignes valides (regles metier) : {df['valide'].sum()} / {len(df)}",
        f"- Valeurs manquantes score_similarite : {df['score_similarite'].isna().sum()} "
        f"(toutes issues de S2)",
        f"- Lignes corrigees suite au bugfix decoupage region/footer : "
        f"{df['corrige_bug_decoupage_region'].sum()}",
    ]

    FICHIER_DICTIONNAIRE.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_DICTIONNAIRE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"Dictionnaire de donnees genere dans : {FICHIER_DICTIONNAIRE}")


def exporter(df):
    """Exporte le dataset final en CSV, JSON et SQLite (les 3 formats
    explicitement cites section 4 : 'CSV/JSON/SQLite')."""
    df.to_csv(FICHIER_NETTOYE_CSV, index=False, encoding="utf-8-sig")
    print(f"Export CSV : {FICHIER_NETTOYE_CSV}")

    df_json = df.copy()
    df_json["timestamp"] = df_json["timestamp"].astype("string")
    df_json.to_json(FICHIER_NETTOYE_JSON, orient="records", force_ascii=False, indent=2)
    print(f"Export JSON : {FICHIER_NETTOYE_JSON}")

    df_sqlite = df.copy()
    df_sqlite["timestamp"] = df_sqlite["timestamp"].astype("string")
    df_sqlite["categorie"] = df_sqlite["categorie"].astype("string")
    df_sqlite["source"] = df_sqlite["source"].astype("string")
    with sqlite3.connect(FICHIER_NETTOYE_SQLITE) as conn:
        df_sqlite.to_sql("interactions", conn, if_exists="replace", index=False)
    print(f"Export SQLite : {FICHIER_NETTOYE_SQLITE}")


def main():
    print("Chargement et fusion S2 + S3...")
    df = charger_et_fusionner()
    print(f"{len(df)} enregistrements charges au total\n")

    df = appliquer_corrections_confusion_villes(df)
    print()

    df = enrichir_avec_timestamp(df)
    df = dedupliquer(df)
    df.to_csv(FICHIER_BRUT_FUSIONNE, index=False, encoding="utf-8-sig")
    print(f"Dataset brut fusionne sauvegarde dans : {FICHIER_BRUT_FUSIONNE}\n")

    df = typer_les_champs(df)
    df = valider_regles_metier(df)

    print()
    generer_dictionnaire_donnees(df)
    print()
    exporter(df)

    print(f"\nNettoyage termine. {len(df)} enregistrements dans le dataset final.")


if __name__ == "__main__":
    main()