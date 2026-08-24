# Architecture du pipeline
 
## Vue d'ensemble
Cascade Selenium → OCR → OmniParser, chaque étage jugé par un LLM local
(Llama 3.2 3B via Ollama). La couche suivante n'intervient que si la
précédente est jugée insuffisante par une heuristique rapide
(resultats_non_vides) ou, pour l'OCR, après tentative de correction du
texte bruité.
 
## Schéma de la cascade
1. Selenium extrait le DOM (+ images du DOM via OmniParser si le
   texte seul est insuffisant)
2. Si insuffisant : capture d'écran, lecture OCR, correction par le
   LLM (avec garde-fous anti-invention et anti-refus)
3. Si toujours insuffisant : analyse OmniParser de la capture complète
   (dernier recours, formulation systématique)
 
## Rôle de chaque module
- src/selenium_layer/ : navigation, extraction DOM, images du DOM
- src/ocr_layer/ : lecture et classification du texte OCR
- src/omniparser_layer/ : détection et classification d'éléments UI
- src/orchestrator_layer/ : prompts, appels LLM, cascade complète
- src/cleaning/ : nettoyage, déduplication, validation
- src/storage/ : export JSON/CSV/SQLite
- src/reports/ : génération de rapport HTML/PDF
 
## Décisions techniques notables
- Modèle LLM : Llama 3.2 3B (remplace Phi-3 Mini, jugé insuffisamment
  fiable sur les tâches de formulation contrainte)
- Génération PDF : impression native Chrome (CDP), pas WeasyPrint
  (conflit de DLL constaté avec Tesseract-OCR sous Windows)
- Résolution ChromeDriver : Selenium Manager (automatique), plus de
  binaire géré manuellement
- Repli sur panne LLM : données brutes renvoyées, jamais de supposition
  silencieuse sur la suffisance des données
