import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# Chemins
LOG_FILE = "data/processed/interactions_log.csv"
OUTPUT_DIR = "docs/figures"

def main():
    print("--- Démarrage de l'analyse Machine Learning des logs RAG ---")
    
    if not os.path.exists(LOG_FILE):
        print(f"Erreur : Le fichier {LOG_FILE} n'existe pas encore.")
        print("Veuillez poser quelques questions dans l'application Streamlit d'abord.")
        return

    # 1. Chargement des données
    df = pd.read_csv(LOG_FILE)
    print(f"Données chargées : {len(df)} interactions trouvées.")

    if len(df) < 4:
        print("\n/!\ ATTENTION : Il y a très peu de questions dans le log.")
        print("Le Machine Learning sera plus pertinent si vous posez d'abord 5 à 10 questions variées dans l'application (des questions dans le contexte, et d'autres hors-contexte).")

    # Nettoyage des valeurs manquantes pour l'analyse numérique
    features_num = ['score_similarite', 'temps_reponse_secondes']
    df_clean = df.dropna(subset=features_num).copy()

    if len(df_clean) < 2:
        print("Pas assez de données numériques valides pour le clustering.")
        return

    # 2. Preprocessing (Standardisation)
    # Indispensable avant un K-Means pour que les secondes et les scores (0 à 1) soient sur la même échelle
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_clean[features_num])

    # 3. Modélisation : Clustering K-Means
    # On force 2 ou 3 clusters selon le nombre de données disponibles
    n_clusters = 3 if len(df_clean) >= 6 else 2
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df_clean['Cluster'] = kmeans.fit_predict(X_scaled)

    # 4. Analyse NLP basique (Mots clés des requêtes par TF-IDF)
    print("\nExtraction des mots-clés les plus fréquents (TF-IDF)...")
    try:
        vectorizer = TfidfVectorizer(stop_words=['le', 'la', 'les', 'un', 'une', 'des', 'est', 'et', 'en', 'de', 'pour'])
        tfidf_matrix = vectorizer.fit_transform(df_clean['question'].fillna(''))
        feature_names = vectorizer.get_feature_names_out()
        mots_importants = sorted(zip(vectorizer.idf_, feature_names))[:5]
        print("Mots les plus caractéristiques posés par les utilisateurs :")
        for score, mot in mots_importants:
            print(f" - {mot}")
    except Exception as e:
        print("Pas assez de texte pour le TF-IDF.")

    # 5. Visualisation Haute Résolution
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Amélioration du style visuel
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 8))
    
    sns.scatterplot(
        data=df_clean, 
        x='score_similarite', 
        y='temps_reponse_secondes', 
        hue='Cluster', 
        palette='Set1',
        s=80,             # Taille des points réduite pour mieux voir l'accumulation
        alpha=0.7,        # Semi-transparence
        edgecolor=None
    )
    
    plt.title("Clustering (K-Means) des requêtes RAG", fontsize=18, pad=20, fontweight='bold')
    plt.xlabel("Score de Similarité Vectorielle (Proximité sémantique)", fontsize=14)
    plt.ylabel("Temps de réponse de l'IA (secondes)", fontsize=14)
    
    # Rendre la légende plus propre
    plt.legend(title="Cluster (Groupe K-Means)", title_fontsize='13', fontsize='12', loc='upper right')

    output_path = os.path.join(OUTPUT_DIR, "analyse_kmeans_rag.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\\nAnalyse terminee ! Le graphique a ete genere avec succes en haute resolution.")
    print(f"Vous pouvez le consulter ici : {output_path}")

if __name__ == '__main__':
    main()
