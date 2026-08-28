# Note de cadrage — Semaine 1 (Initialisation & Setup)

**Stage M1 Data Science — YB-TECHs**
**Sujet :** Agent d'Analyse et de Valorisation des Interactions d'un Système RAG
**Étudiant :** Janvion Hamayadji
**Encadrement :** Yris Brice Wandji Piugie, PhD — Fondateur & CEO, YB-TECHs
**Date :** Semaine 1 — Juillet 2026

---

## 1. Thème documentaire retenu

**Microfinance au Cameroun**

Ce thème a été resserré volontairement au périmètre national camerounais (plutôt qu'une portée continentale/africaine) pour les raisons suivantes :
- **Cohérence réglementaire** : le secteur de la microfinance au Cameroun est encadré par un corpus réglementaire unique et bien identifié (COBAC/CEMAC), ce qui garantit l'homogénéité du corpus documentaire
- **Richesse documentaire suffisante** : le secteur camerounais dispose de sources précises, récentes et vérifiables (textes réglementaires, statistiques officielles, institutions nommées), sans besoin d'élargir à d'autres pays
- **Pertinence pour les tests "hors périmètre"** : en limitant le corpus au Cameroun, il devient possible de tester volontairement des requêtes portant sur d'autres pays (ex. Sénégal, Kenya) pour évaluer la capacité de l'agent à ne pas halluciner en dehors de son périmètre documentaire — un cas de test explicitement demandé en section 3.2 du spécifications
- **Pertinence pour YB-TECHs** : cohérent avec l'implantation de l'entreprise à Yaoundé et son positionnement sur les marchés francophones d'Afrique

## 2. Corpus documentaire envisagé (15-20 documents)

**Cadre réglementaire et institutionnel (cœur du corpus)**
- Réglementation COBAC sur la microfinance (BEAC)
- Règlement COBAC n°01/17/CEMAC/UMAC/COBAC du 27 septembre 2017 (conditions d'exercice et de contrôle)
- Guide sur l'agrément des établissements de microfinance (EMF) au Cameroun
- Classification des EMF par catégories (1, 2, 3) et principaux acteurs (CamCCUL, MC2, ACEP, Express Union Finance, La Régionale)
- Statistiques officielles sur le nombre d'EMF agréés et le volume de crédits du secteur (source : MINFI/COBAC, relayée par la presse économique)
- Réforme du contrôle COBAC (2015) et renforcement de la supervision prudentielle

**Sources encyclopédiques (Wikipédia FR — définitions générales)**
- Microfinance
- Microcrédit
- Tontine
- Institution de microfinance
- Grameen Bank (référence historique/comparative, hors périmètre Cameroun — utile pour tester la distinction)

**Sources institutionnelles locales (registre pratique)**
- Page institutionnelle CamCCUL (réseau de coopératives d'épargne et de crédit)
- Page institutionnelle MC2 (réseau de microfinance rurale camerounaise)
- Page institutionnelle Express Union Finance

**Compléments optionnels (si besoin d'atteindre 20 documents)**
- Articles de presse économique sur le surendettement lié aux EMF
- Articles sur les faillites d'EMF et la protection des épargnants
- Statistiques de répartition régionale des EMF au Cameroun (Centre, Littoral, Extrême-Nord, etc.)

## 3. Contraintes matérielles identifiées

| Ressource | Caractéristique | Impact |
|---|---|---|
| CPU | Intel i5-7200U (2 cœurs / 4 threads, 2.50GHz) | Pas d'accélération GPU disponible |
| RAM | 8 Go (souvent ~88% utilisée en usage courant) | Contrainte forte sur la taille du LLM local |
| GPU | Aucun GPU dédié (graphique intégré uniquement) | Inférence 100% CPU |
| Stockage | 50,9 Go libres sur C: | Non contraignant |

### Ajustement technique proposé et communiqué au tuteur
Le spécifications recommande Mistral 7B-Instruct ou Llama 3.1 8B comme LLM local. Ces modèles se sont révélés impraticables sur la configuration matérielle disponible (temps de réponse de plusieurs minutes, saturation mémoire). Un modèle plus léger, **Llama 3.2 3B** (quantifié, via Ollama), a été retenu comme alternative :
- Reste dans la famille Llama, respecte l'esprit du spécifications (LLM local, sans clé API, via Ollama)
- Temps de réponse mesuré : ~8 secondes sans contexte, ~40 secondes avec contexte injecté (scénario RAG réaliste)
- Fidélité au contexte fourni jugée satisfaisante lors des tests préliminaires

Cette limite matérielle sera documentée et discutée dans le rapport de stage final (section "Résultats, discussion et limites du système"), notamment son impact potentiel sur la fiabilité de l'évaluation RAGAS.

## 4. Environnement technique mis en place

- Python 3.11.15 (Conda, environnement dédié `rag-stage`)
- Ollama + Llama 3.2 3B (quantifié Q4)
- Stack RAG : LangChain, FAISS/ChromaDB, sentence-transformers
- Évaluation : RAGAS (avec correctif de compatibilité documenté et versionné — `src/ragas_compat.py`)
- Modélisation : scikit-learn
- Restitution : Streamlit
- Tests : pytest
- Versionnage : Git, dépôt hébergé sur l'organisation GitHub YB-TECHs

## 5. Prochaines étapes (Semaine 2)

- Constitution effective du corpus (récupération automatisée des pages Wikipédia + textes réglementaires/institutionnels identifiés)
- Chunking et indexation vectorielle du corpus
- Construction de l'agent RAG maison (retriever + prompt template + LLM local)
- Premiers tests de requêtage (30-50 interactions), incluant des requêtes volontairement hors périmètre (autres pays) pour évaluer la robustesse
- Mise en place du journal des interactions (schéma de logs)
