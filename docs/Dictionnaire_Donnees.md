# Dictionnaire de donnees — Dataset d'interactions RAG (S2 + S3)

Genere automatiquement par `src/nettoyage_dataset.py`.
Nombre total d'enregistrements : 310

| Colonne | Type Pandas | Description |
|---|---|---|
| `id` | `string` | Identifiant unique de l'interaction (ex. Q01, S3-042). |
| `categorie` | `category` | Categorie de la question (definitions, reglementation, categories_emf, institutions, geo_tabulaire, scenario, comparaison, chiffres, ambigue, hors_perimetre). |
| `question` | `string` | Texte de la question posee a l'agent RAG. |
| `reponse` | `string` | Texte de la reponse generee par le LLM. |
| `nb_documents_recuperes` | `Int64` | Nombre de chunks retournes par le retriever hybride (BM25+FAISS) apres fusion, borne par MAX_CONTEXTE_CHUNKS. |
| `score_similarite` | `float64` | Score de similarite semantique du meilleur chunk FAISS, normalise entre 0 et 1 via 1/(1+distance_L2). ABSENT pour les interactions S2 (colonne ajoutee apres la campagne de tests S2) : valeurs manquantes (NaN) pour ces lignes, non imputees. |
| `temps_reponse_secondes` | `float64` | Temps total de traitement de la question, en secondes (recuperation + generation LLM). |
| `statut` | `string` | Statut brut de l'execution : 'succes' ou 'echec' (erreur technique lors du traitement). |
| `source` | `category` | Semaine de generation de l'interaction : S2 (campagne de validation initiale, 35 questions) ou S3 (generation massive du dataset, 275 questions). |
| `corrige_bug_decoupage_region` | `bool` | Booleen : True si cette ligne a ete regeneree avec l'index corrige suite a la decouverte d'un bug de decoupage (chunks a cheval sur deux regions, ou pollues par un encart publicitaire). Concerne les cas de confusion de ville identifies par verifier_confusion_villes.py puis corriges par corriger_reponses_confuses.py. |
| `timestamp` | `datetime64[us]` | Date et heure de l'interaction, recuperee depuis le journal maitre (data/processed/interactions_log.csv) par correspondance sur le texte de la question. Absent (NaT) si aucune correspondance trouvee. |
| `succes` | `bool[pyarrow]` | Booleen derive de 'statut' : True si statut == 'succes', False sinon. |
| `valide` | `boolean` | Booleen issu de la validation par regles metier (section 4) : True si score_similarite dans [0,1] (ou absent), temps_reponse_secondes > 0, et nb_documents_recuperes >= 0. |

## Statistiques rapides

- Repartition par source : {'S3': 275, 'S2': 35}
- Repartition par categorie : {'geo_tabulaire': 65, 'scenario': 58, 'reglementation': 47, 'definitions': 35, 'hors_perimetre': 25, 'ambigue': 20, 'comparaison': 20, 'chiffres': 18, 'institutions': 17, 'categories_emf': 5}
- Taux de succes global : 100.0%
- Lignes valides (regles metier) : 310 / 310
- Valeurs manquantes score_similarite : 34 (toutes issues de S2)
- Lignes corrigees suite au bugfix decoupage region/footer : 8