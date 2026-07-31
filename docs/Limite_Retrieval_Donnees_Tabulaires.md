# Résolution : retrieval sur données tabulaires (Semaine 2)

**Agent RAG Microfinance au Cameroun**

## Contexte

Le corpus inclut un document PDF listant les établissements de microfinance
agréés au Cameroun (`LISTE-DES-EMF-AGREES-CAMEROUN.pdf`), structuré sous
forme de tableau : numéro, dénomination, localisation, dirigeants, numéro
d'agrément, numéro d'immatriculation.

## Symptôme initial

Une question comme *"Quelles sont les microfinances présentes à Maroua ?"*
obtenait systématiquement une réponse en abstention ("Je ne dispose pas de
cette information dans mes documents"), alors même que l'information
existait bien dans le corpus indexé (confirmé par une recherche directe
dans l'index FAISS).

## Démarche de diagnostic et corrections successives

Le problème s'est révélé être la superposition de **quatre bugs distincts**,
découverts un par un par isolation méthodique (tester chaque composant du
pipeline séparément : le retriever seul, sans le LLM ; BM25 seul, sans la
fusion ; etc.).

### 1. Recherche sémantique seule insuffisante sur données tabulaires

Le texte extrait d'un tableau PDF perd sa structure en colonnes lors de
l'extraction (`PyPDFLoader`/`pypdf`) : les champs Numéro, Dénomination,
Localisation, Dirigeants, Agrément se retrouvent concaténés dans un ordre
qui ne forme pas des phrases grammaticalement cohérentes. Un modèle
d'embedding sémantique (`paraphrase-multilingual-MiniLM-L12-v2`) rapproche
mal ce type de contenu fragmenté d'une question posée en langage courant.

**Correction** : ajout d'un retriever hybride combinant recherche
sémantique (FAISS) et recherche par mot-clé exact (BM25, via
`EnsembleRetriever`), qui retrouve directement un chunk contenant un nom
de ville même si sa structure nuit à l'embedding sémantique.

### 2. Sensibilité à la casse de BM25

Par défaut, `BM25Retriever` tokenise le texte avec un simple `text.split()`,
**sans mise en minuscule**. Une question tapée `"maroua"` ne correspondait
donc pas au document contenant `"Maroua"` — deux tokens différents du
point de vue de la comparaison exacte de chaînes.

**Correction** : ajout d'un `preprocess_func` personnalisé mettant tout en
minuscule, appliqué à la fois lors de l'indexation et de chaque requête.

### 3. Dilution du signal par les mots vides (stopwords)

M�me après correction de la casse, une question complète en langage
naturel ("quelles sont les microfinances presentes a maroua ?") contient
des mots très fréquents dans le corpus ("quelles", "sont", "les", "a").
Le score BM25 cumulé de ces mots courants noyait le signal du seul mot
réellement discriminant ("maroua", présent dans seulement 2 chunks sur
718).

**Correction** : retrait des mots vides français avant le calcul du score,
pour que les mots-clés spécifiques (villes, sigles, institutions)
dominent le classement.

### 4. Incohérence des accents

Un diagnostic plus poussé (mesure du **rang exact** du bon chunk dans le
classement BM25 complet) a révélé un cas encore plus retors avec
Yaoundé : la question tapée sans accent ("Yaounde") ne correspondait pas
au document contenant l'accent ("Yaoundé"), faisant chuter le rang du bon
chunk de la 9ème position (cas Maroua, sans accent) à la **265ème
position** (cas Yaoundé, avec accent) — bien au-delà du nombre de chunks
retenus par BM25.

**Correction** : normalisation Unicode (`unicodedata.normalize("NFD", ...)`)
retirant systématiquement les accents avant comparaison, aussi bien à
l'indexation qu'à la requête. Après correction, le rang du meilleur chunk
Yaoundé est passé de 265 à 8.

### 5. Troncature silencieuse du contexte par Ollama

Une fois le retrieval corrigé (les bons chunks bien présents parmi les
documents récupérés), le modèle continuait pourtant à répondre "je ne
dispose pas de cette information" pour Yaoundé. Cause : Ollama limite par
défaut la fenêtre de contexte à **2048 tokens**, quel que soit le modèle
utilisé. Avec 20 à 25 chunks récupérés (~800 caractères chacun), le
prompt final dépassait largement cette limite, et Ollama tronquait
silencieusement le contexte — sans aucune erreur ni avertissement. Les
chunks pertinents, s'ils tombaient dans la partie coupée, n'étaient
alors jamais vus par le modèle.

**Correction** : augmentation explicite de `num_ctx` à 8192 lors de
l'instanciation du LLM (`Ollama(model=LLM_MODEL, num_ctx=8192)`).

## Résultat final

Après ces cinq corrections cumulées, une question comme *"quelles sont
les microfinances qu'on trouve à Yaoundé ?"* obtient une réponse correcte
et sourcée, citant plusieurs institutions réellement présentes dans le
corpus (SOCEC, MUCADEC, MUFFEDYC, BFI, CEPI SA...), sans invention de
noms fictifs.

## Compromis assumé : temps de réponse

Ces corrections augmentent le nombre de chunks récupérés (jusqu'à ~25) et
la fenêtre de contexte du modèle, ce qui allonge le temps de réponse
(environ 250 à 350 secondes sur le matériel utilisé, contre 40-80
secondes avec un retrieval plus restreint mais incomplet). Ce compromis
est jugé acceptable à ce stade du projet : mieux vaut une réponse
correcte mais lente qu'une réponse rapide mais fausse ou en abstention
injustifiée. Une piste d'optimisation ultérieure (hors périmètre S2)
serait de ne déclencher l'élargissement du contexte (BM25_K plus grand,
num_ctx plus grand) que lorsque la question contient un indice
géographique ou nominatif détecté au préalable.

## Valeur méthodologique de cette démarche

Ce cas illustre une méthode de diagnostic RAG en couches : à chaque
étape, isoler un composant du pipeline (retriever seul, BM25 seul, rang
exact dans le classement, contenu réel du contexte envoyé au LLM) a
permis d'identifier précisément quel maillon de la chaîne était en
cause, plutôt que de multiplier des ajustements à l'aveugle. Chaque bug
pris isolément est mineur ; leur superposition suffisait à provoquer un
échec total et silencieux du système.
