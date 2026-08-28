# Agent RAG — Microfinance au Cameroun

**Stage M1 Data Science — YB-TECHs**
*Agent d'Analyse et de Valorisation des Interactions d'un Système RAG*
* **Étudiant** : Janvion Hamayadji
* **Encadrement** : Yris Brice Wandji Piugie, PhD — Fondateur & CEO, YB-TECHs
* **Durée** : 2 mois (Juillet–Août 2026)

## Présentation du projet
Ce projet vise à concevoir une architecture complète allant de la collecte documentaire à l'évaluation et la valorisation par Machine Learning des données d'interaction d'un système RAG (Retrieval-Augmented Generation). L'objectif est de transformer un système RAG « boîte noire » en un produit final pilotable, mesurable et interrogeable via une interface web interactive.

**Thème documentaire** : Microfinance au Cameroun (réglementation COBAC, annuaire des établissements de microfinance agréés, pratiques locales telles que la tontine/ndjangui).

## Architecture du pipeline
Corpus documentaire → Chunking & Indexation Hybride (FAISS + BM25) → Agent RAG & Interface Web (Streamlit) → Journal d'interactions → Nettoyage (Pandas) → Clustering Machine Learning (Scikit-Learn).

## Structure principale du dépôt
```text
.
├── data/
│   ├── raw/                # Corpus documentaire brut (PDF, TXT)
│   └── processed/          # Index FAISS, journaux (interactions_log.csv), datasets
├── docs/
│   └── figures/            # Graphiques générés par le ML (analyse_kmeans_rag.png)
├── src/
│   ├── build_index.py      # Chunking + indexation vectorielle
│   ├── rag_agent.py        # Moteur RAG (retriever hybride BM25+FAISS avec MMR)
│   ├── app_streamlit.py    # Interface Web interactive avec traçabilité des sources
│   ├── analyse_ml_logs.py  # Clustering K-Means et TF-IDF sur les logs du RAG
│   ├── recherche_exhaustive_ville.py # Recherche tabulaire exacte (annuaire EMF)
│   ├── nettoyage_dataset.py# Nettoyage Pandas et structuration
│   └── ...                 # Scripts de génération de datasets (S2/S3)
├── requirements.txt        # Dépendances de l'environnement Python
└── README.md
```

## Stack Technique
| Technologie | Rôle |
|---|---|
| **Python 3.11** | Langage principal |
| **Ollama (Llama 3.2 3B)** | LLM local (optimisé pour environnement sans GPU dédié) |
| **LangChain** | Orchestration du pipeline RAG |
| **FAISS & BM25** | Base vectorielle et algorithme de recherche par mots-clés |
| **sentence-transformers** | Modèle de plongement lexical (Embeddings) |
| **Streamlit** | Interface graphique web avec fonctionnalités d'export des sources |
| **Scikit-Learn** | Modélisation non-supervisée (Clustering K-Means, analyse NLP TF-IDF) |
| **Pandas** | Traitement, nettoyage et ingénierie des données des logs |
| **RAGAS & Pytest** | Évaluation des métriques RAG et tests unitaires |

## Installation & Prérequis

* Python 3.11 (via Conda recommandé)
* [Ollama](https://ollama.com/) installé et lancé localement

```bash
# Cloner le dépôt
git clone https://github.com/YB-TECHs/Agent_GUI_Web.git
cd Agent_GUI_Web

# Créer et activer l'environnement Conda
conda create -n rag-stage python=3.11
conda activate rag-stage

# Installer les dépendances
pip install -r requirements.txt

# Télécharger le modèle LLM local
ollama pull llama3.2:3b
```

## Utilisation

### 1. Indexation du corpus
Avant la première utilisation, ou si vous ajoutez de nouveaux fichiers PDF/TXT dans le dossier `data/raw/`, mettez à jour la base de données hybride :
```bash
python src/build_index.py
```

### 2. Lancement de l'Application Web
L'interaction avec l'agent s'effectue via une interface Streamlit ergonomique. Le système fournit une réponse générée par l'IA ainsi que la possibilité de télécharger directement les fichiers sources utilisés pour la génération :
```bash
streamlit run src/app_streamlit.py
```

### 3. Modélisation et Analyse des Logs (Machine Learning)
Chaque interaction est silencieusement enregistrée dans `interactions_log.csv` avec ses métriques (temps de réponse, score de similarité vectorielle). Pour exécuter l'algorithme de clustering sur ces données :
```bash
python src/analyse_ml_logs.py
```
*Le script génère une analyse TF-IDF des questions récurrentes et exporte une cartographie de clustering (K-Means) dans le dossier `docs/figures/`.*

### 4. Tests et Génération de Dataset (S3)
Pour rejouer les campagnes de tests formels (S2/S3) et générer les rapports Pandas de nettoyage :
```bash
python src/generer_questions_dataset.py
python src/generer_dataset_S3.py
python src/nettoyage_dataset.py
```
*Note : Ces processus peuvent prendre plusieurs heures selon le CPU de la machine.*

## Documentation des Sprints
* [Note de cadrage (Semaine 1)](docs/Note_de_cadrage_S1.md)
* [Limite du retrait sur données tabulaires (Semaine 2)](docs/Limite_Retrieval_Donnees_Tabulaires.md)
* [Conclusion de la Semaine 2](docs/Conclusion_Semaine_2.md)
* [Dictionnaire de données du dataset final (Semaine 3)](docs/Dictionnaire_Donnees.md)

## Licence
Projet réalisé dans le cadre d'un stage de Master 1 Data Science sous la supervision exclusive de YB-TECHs. Reproduction ou utilisation soumises à autorisation.
