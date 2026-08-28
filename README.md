# Agent RAG — Microfinance au Cameroun

Stage M1 Data Science — YB-TECHs
Agent d'Analyse et de Valorisation des Interactions d'un Système RAG

**Étudiant :** Janvion Hamayadji
**Encadrement :** Yris Brice Wandji Piugie, PhD — Fondateur & CEO, YB-TECHs
**Durée :** 2 mois (Juillet–Août 2026)

---

## Présentation du projet

Ce projet vise à concevoir une architecture unique et intégrée de collecte, d'évaluation et de valorisation des données d'interaction d'un système RAG (Retrieval-Augmented Generation), afin de transformer un système RAG « boîte noire » en un système pilotable, mesurable et interrogeable en langage naturel.

**Thème documentaire :** Microfinance au Cameroun (réglementation COBAC, établissements de microfinance agréés, institutions locales).

## Architecture du pipeline

```
Corpus documentaire → Agent RAG maison → Journal d'interactions
→ Nettoyage (Pandas) → Évaluation (RAGAS) → Modélisation (scikit-learn)
→ Indexation → Dashboard + Copilot conversationnel
```

## Structure du dépôt

```
.
├── data/
│   ├── raw/                              # Corpus documentaire brut (non versionné, voir .gitignore)
│   └── processed/                        # Index FAISS, journaux, datasets (non versionné)
├── docs/
│   ├── Note_de_cadrage_S1.md
│   ├── Limite_Retrieval_Donnees_Tabulaires.md
│   ├── Conclusion_Semaine_2.md
│   └── Dictionnaire_Donnees.md            # Genere par nettoyage_dataset.py
├── notebooks/                             # Notebooks Jupyter (EDA, RAGAS, modélisation — a venir S4+)
├── src/
│   ├── fetch_corpus.py                    # S1 — recuperation du corpus Wikipedia
│   ├── build_index.py                     # S1/S2 — chunking + indexation FAISS
│   ├── rag_agent.py                       # S2 — agent RAG (retriever hybride BM25+FAISS)
│   ├── run_test_questions.py              # S2 — campagne de test (30-50 questions)
│   ├── analyser_resultats_S2.py           # S2 — resume statistique
│   ├── generer_questions_dataset.py       # S3 — generation de la liste de questions (>=300)
│   ├── generer_dataset_S3.py              # S3 — execution resumable de la campagne
│   ├── verifier_confusion_villes.py       # S3 — QA : detection de confusions de ville
│   ├── corriger_reponses_confuses.py      # S3 — regeneration ciblee post-bugfix
│   ├── recherche_exhaustive_ville.py      # Outil complementaire : recherche exhaustive
│   ├── nettoyage_dataset.py               # S3 — nettoyage Pandas + export final
│   └── ragas_compat.py                    # Correctif de compatibilité RAGAS
├── tests/
│   ├── unit/                              # Tests pytest formels
│   └── diagnostics/                       # Scripts de débogage ponctuels (hors pipeline)
├── test_questions.csv                     # Questions de test S2
├── questions_dataset_S3.csv               # Questions generees pour S3
├── requirements.txt                       # Dépendances exactes de l'environnement Python
└── README.md
```

## Stack technique

| Outil | Rôle |
|---|---|
| Python 3.11 | Langage principal |
| Ollama + Llama 3.2 3B | LLM local (voir justification ci-dessous) |
| LangChain | Orchestration du pipeline RAG |
| FAISS / ChromaDB | Base vectorielle |
| sentence-transformers | Embeddings |
| Pandas | Nettoyage et structuration des données |
| RAGAS | Évaluation de la qualité RAG |
| scikit-learn | Modélisation légère (scoring / clustering) |
| Streamlit | Dashboard et interface Copilot |
| pytest | Tests unitaires et d'intégration |

### Note sur le choix du LLM local

Le spécifications recommande Mistral 7B-Instruct ou Llama 3.1 8B. Compte tenu d'une contrainte matérielle réelle (CPU sans GPU dédié, 8 Go de RAM), **Llama 3.2 3B** a été retenu comme alternative, validée avec le tuteur. Cette décision est documentée dans `docs/Note_de_cadrage_S1.md` et sera discutée dans le rapport final (section limites du système).

## Installation

### Prérequis
- Python 3.11 (via Conda recommandé)
- [Ollama](https://ollama.com) installé localement
- Git

### Mise en place de l'environnement

```bash
# Cloner le dépôt
git clone https://github.com/YB-TECHs/<nom-du-depot>.git
cd <nom-du-depot>

# Créer l'environnement Conda
conda create -n rag-stage python=3.11
conda activate rag-stage

# Installer les dépendances
pip install -r requirements.txt

# Télécharger le modèle LLM local
ollama pull llama3.2:3b
```

### Correctif de compatibilité RAGAS

`ragas` 0.3.9 contient un bug de compatibilité connu avec les versions récentes de `langchain-community` (import cassé vers `langchain_community.chat_models.vertexai`). Un correctif est appliqué automatiquement via `src/ragas_compat.py`, qui doit être importé **avant** tout import de `ragas` :

```python
import sys
sys.path.insert(0, "src")
import ragas_compat  # doit précéder l'import de ragas
import ragas
```

Aucune action manuelle supplémentaire n'est requise après `pip install -r requirements.txt`.

### Évaluation RAGAS locale

Le pilote RAGAS utilise `llama3.2:3b` via `src/ollama_ragas.py`. Cet adaptateur
envoie les schémas JSON de RAGAS directement à Ollama afin d'obtenir des sorties
structurées fiables. La précision du contexte est calculée sur les quatre premiers
passages récupérés (`Context Precision@4`) pour rester compatible avec la capacité
de la machine locale.

Pour valider une seule interaction avant le pilote complet :

```powershell
$env:RAGAS_TAILLE_PILOTE = "1"
python src/ragas_pilote.py
Remove-Item Env:RAGAS_TAILLE_PILOTE
```

## Utilisation

Cette section decrit l'ordre exact d'execution du pipeline, du corpus brut
au dataset final structure (Semaines 1 a 3). Chaque etape suppose que la
precedente a ete executee avec succes.

### Etape 1 — Constitution du corpus et indexation (Semaine 1-2)

```bash
# Recupere les pages Wikipedia du corpus (deja fait, resultat versionne
# dans data/raw/ ; a relancer uniquement si le corpus doit etre regenere)
python src/fetch_corpus.py

# Construit l'index vectoriel FAISS a partir de tous les fichiers .txt/.pdf
# presents dans data/raw/
python src/build_index.py
```

### Etape 2 — Agent RAG interactif (Semaine 2)

```bash
python src/rag_agent.py
```

Lance une session de questions/reponses en ligne de commande. Tape `exit`
pour quitter. Chaque interaction est journalisee automatiquement dans
`data/processed/interactions_log.csv`.

### Etape 3 — Campagne de test S2 (30-50 questions, spécifications section 9)

```bash
python src/run_test_questions.py
python src/analyser_resultats_S2.py
```

Le premier script pose automatiquement les questions listees dans
`test_questions.csv` et journalise les resultats dans
`data/processed/resultats_tests_S2.csv`. Le second produit un resume
statistique (temps de reponse, taux d'abstention par categorie).

### Etape 4 — Generation du dataset complet S3 (>= 300 interactions, spécifications section 9)

```bash
python src/generer_questions_dataset.py
python src/generer_dataset_S3.py
```

Le premier script genere `questions_dataset_S3.csv` : il detecte
**automatiquement** les villes et institutions reellement presentes dans
le corpus indexe (pas de question generee a l'aveugle sur une entite
absente), et plafonne le nombre de questions geo_tabulaire pour garantir
une repartition equilibree entre categories.

Le second script pose ces questions et journalise les resultats dans
`data/processed/dataset_interactions_S3.csv`. **module est resumable** :
en cas d'interruption (fermeture, coupure), le relancer simplement reprend
la ou il s'etait arrete, sans dupliquer ni perdre de travail deja effectue.

⚠️ Duree d'execution : plusieurs heures sur une machine sans GPU (compter
~100-200s par question). A executer sur plusieurs sessions si necessaire.

### Etape 5 — Verification de qualite et outil de recherche exhaustive (optionnel, recommande)

```bash
# Detecte automatiquement les confusions de ville dans les reponses
# generees (ex. un etablissement de Garoua cite a tort dans une reponse
# sur Douala), sans recalcul, par analyse du texte deja enregistre
python src/verifier_confusion_villes.py

# Recherche exhaustive de tous les etablissements d'une ville donnee,
# SANS passer par le LLM (complement fiable au chat pour un usage reel,
# le RAG classique n'etant pas concu pour l'enumeration exhaustive)
python src/recherche_exhaustive_ville.py NomDeLaVille
```

Si `verifier_confusion_villes.py` signale des confusions, elles peuvent
etre corrigees avec l'index reconstruit (voir note ci-dessous) :

```bash
python src/corriger_reponses_confuses.py
```

module ne modifie **jamais** les fichiers bruts (`resultats_tests_S2.csv`,
`dataset_interactions_S3.csv`) : il produit un fichier de corrections
separe (`data/processed/corrections_confusion_villes.csv`), applique
ensuite de facon **tracee** par le script de nettoyage (colonne
`corrige_bug_decoupage_region`).

### Etape 6 — Nettoyage et structuration finale (Semaine 3, spécifications section 4)

```bash
python src/nettoyage_dataset.py
```

Fusionne S2 + S3, applique les corrections eventuelles (etape 5),
deduplique, type explicitement chaque champ (y compris un booleen
succes/echec), valide par regles metier (score de similarite entre 0 et 1,
temps de reponse positif), et exporte le dataset final en CSV/JSON/SQLite,
accompagne d'un dictionnaire de donnees (`docs/Dictionnaire_Donnees.md`).

### Suite de tests (pytest)

```bash
pip install pytest-cov
pytest tests/unit/ -v
pytest --cov=src tests/
```

Les scripts de debogage ponctuels utilises pendant le developpement
(`tests/diagnostics/`) sont distincts des tests pytest formels
(`tests/unit/`) et ne sont pas necessaires a l'execution du pipeline.

### Note importante sur la reutilisation de ce travail

Les scripts `generer_questions_dataset.py`, `verifier_confusion_villes.py`
et `corriger_reponses_confuses.py` contiennent des listes de villes et
d'institutions **specifiques au corpus microfinance Cameroun**
(constantes `VILLES_CANDIDATES` et `INSTITUTIONS_A_VERIFIER`). Elles
sont deja adaptees a ce projet et n'ont besoin d'aucune modification pour
reproduire ce travail tel quel, conformement a l'objectif de
reproductibilite du spécifications (section 1.3 et 10.1).

## Documentation

- [Note de cadrage (Semaine 1)](docs/Note_de_cadrage_S1.md)
- [Limite du retrieval sur données tabulaires (Semaine 2)](docs/Limite_Retrieval_Donnees_Tabulaires.md)
- [Conclusion de la Semaine 2](docs/Conclusion_Semaine_2.md)
- [Dictionnaire de données du dataset final (Semaine 3)](docs/Dictionnaire_Donnees.md)

## Licence

*(À préciser selon les consignes de YB-TECHs)*
