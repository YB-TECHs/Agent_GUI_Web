# Agent Intelligent GUI/Web avec RAG — YB-TECHs

Stage M1 Data Science · Vadeïl · ENSPM INFOTEL · Juillet 2026  
Encadrant : Yris Brice Wandji Piugie, PhD · Fondateur & CEO, YB-TECHs

## Description
Pipeline d'extraction de données tri-couche piloté par LLM local (Phi-3 Mini).

## Versions
- **Version A** (`src/`) : pipeline Selenium + OCR + OmniParser sans RAG
- **Version B** (`src/rag_*`) : pipeline augmenté par mémoire vectorielle (ChromaDB + LangChain)

## Structure
```
src/
├── selenium_layer/      # Couche 1 : automatisation web
├── ocr_layer/           # Couche 2 : lecture de documents
├── omniparser_layer/    # Couche 3 : analyse d'interfaces GUI
├── orchestrator/        # LLM Phi-3 Mini via Ollama
├── cleaning/            # Nettoyage et normalisation Pandas
├── storage/             # Stockage JSON/CSV/SQLite
├── rag_p1_memory/       # RAG Point 1 : mémoire des trajectoires
└── rag_p3_query/        # RAG Point 3 : interface Q&R Streamlit
```
## Environnements
- `agent_pipe/` : environnement virtuel pipeline principal (Python 3.11)
- `agent_pipe_rag/` : environnement virtuel couche RAG (Python 3.11)