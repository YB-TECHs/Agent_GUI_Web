# audit_dataset.py
import pandas as pd
import numpy as np
import json
from pathlib import Path

print("="*60)
print("🔍 AUDIT COMPLET DU DATASET")
print("="*60)

# 1. Charger le dataset principal
dataset_path = Path("data/processed/dataset_final_nettoye.csv")
if not dataset_path.exists():
    dataset_path = Path("data/processed/dataset_interactions_S3.csv")

if not dataset_path.exists():
    print("❌ Aucun dataset trouvé !")
    exit()

print(f"\n📁 Fichier: {dataset_path}")
df = pd.read_csv(dataset_path)
print(f"📊 Shape: {df.shape[0]} lignes, {df.shape[1]} colonnes")

# 2. Colonnes
print(f"\n📋 Colonnes: {df.columns.tolist()}")

# 3. Types
print(f"\n📋 Types: {df.dtypes.to_dict()}")

# 4. Valeurs manquantes
print(f"\n🔢 Valeurs manquantes par colonne:")
print(df.isnull().sum())

# 5. Doublons
doublons = df.duplicated().sum()
print(f"\n🔄 Doublons: {doublons}")

# 6. Statistiques descriptives
print(f"\n📊 Statistiques descriptives:")
print(df.describe())

# 7. Distribution des statuts
if 'statut' in df.columns:
    print(f"\n📊 Distribution statuts:")
    print(df['statut'].value_counts())

# 8. Vérification du score de similarité (0-1)
if 'score_similarite' in df.columns:
    print(f"\n🎯 Score de similarité (doit être entre 0 et 1):")
    print(f"   Min: {df['score_similarite'].min():.4f}")
    print(f"   Max: {df['score_similarite'].max():.4f}")
    print(f"   Moyenne: {df['score_similarite'].mean():.4f}")
    print(f"   NaN: {df['score_similarite'].isnull().sum()}")

# 9. Temps de réponse
if 'temps_reponse_secondes' in df.columns:
    print(f"\n⏱️ Temps de réponse:")
    print(f"   Min: {df['temps_reponse_secondes'].min():.2f}s")
    print(f"   Max: {df['temps_reponse_secondes'].max():.2f}s")
    print(f"   Moyenne: {df['temps_reponse_secondes'].mean():.2f}s")
    print(f"   NaN: {df['temps_reponse_secondes'].isnull().sum()}")

# 10. Charger les résultats RAGAS (si existant)
ragas_path = Path("data/processed/ragas_pilote_resultats.csv")
if ragas_path.exists():
    print("\n" + "="*60)
    print("📊 AUDIT DES RÉSULTATS RAGAS")
    print("="*60)
    
    df_ragas = pd.read_csv(ragas_path)
    print(f"Shape: {df_ragas.shape}")
    
    # Métriques RAGAS
    ragas_metrics = ['faithfulness', 'answer_relevancy', 'context_precision']
    
    # Vérifier Context Recall
    if 'context_recall' in df_ragas.columns:
        ragas_metrics.append('context_recall')
        print("✅ Context Recall présent (4ème métrique)")
    else:
        print("❌ Context Recall manquant (3/4 métriques seulement)")
    
    for metric in ragas_metrics:
        if metric in df_ragas.columns:
            print(f"\n📈 {metric}:")
            print(f"   Min: {df_ragas[metric].min():.4f}")
            print(f"   Max: {df_ragas[metric].max():.4f}")
            print(f"   Moyenne: {df_ragas[metric].mean():.4f}")
            print(f"   NaN: {df_ragas[metric].isnull().sum()}")
            # Vérifier les valeurs hors plage (0-1)
            invalid = ((df_ragas[metric] < 0) | (df_ragas[metric] > 1)).sum()
            if invalid > 0:
                print(f"   ⚠️ {invalid} valeurs hors plage [0,1]")

# 11. Vérifier le fichier de références
ref_path = Path("data/processed/reference_answers.json")
if ref_path.exists():
    print("\n" + "="*60)
    print("📚 AUDIT DES RÉFÉRENCES")
    print("="*60)
    
    with open(ref_path, 'r', encoding='utf-8') as f:
        references = json.load(f)
    
    print(f"Nombre de références: {len(references)}")
    
    if len(references) >= 30:
        print("✅ Suffisant pour Context Recall (≥30 requis)")
    else:
        print(f"⚠️ Insuffisant ({len(references)}/30 requis)")
    
    # Vérifier le format
    valides = 0
    invalides = 0
    for r in references:
        if isinstance(r, dict) and 'question' in r and 'ground_truth' in r:
            valides += 1
        else:
            invalides += 1
    
    print(f"   Format valide: {valides}")
    print(f"   Format invalide: {invalides}")

# 12. Analyse des clusters (si existant)
cluster_path = Path("data/processed/interactions_with_clusters.csv")
if cluster_path.exists():
    print("\n" + "="*60)
    print("🔍 AUDIT DU CLUSTERING")
    print("="*60)
    
    df_cluster = pd.read_csv(cluster_path)
    if 'cluster' in df_cluster.columns:
        print(f"Distribution des clusters:")
        print(df_cluster['cluster'].value_counts().sort_index())
    else:
        print("❌ Colonne 'cluster' non trouvée")

# 13. Suggestions d'amélioration
print("\n" + "="*60)
print("💡 RÉSUMÉ ET RECOMMANDATIONS")
print("="*60)

issues = []

# Vérification volume
if len(df) < 200:
    issues.append(f"❌ Volume insuffisant: {len(df)}/200 minimum")
elif len(df) < 400:
    issues.append(f"⚠️ Volume moyen: {len(df)}/400 cible")

# Vérification métriques RAGAS
if ragas_path.exists():
    if 'context_recall' not in df_ragas.columns:
        issues.append("❌ Context Recall manquant (3/4 métriques)")
    
    # Vérifier valeurs NaN
    for metric in ['faithfulness', 'answer_relevancy', 'context_precision']:
        if metric in df_ragas.columns:
            nan_count = df_ragas[metric].isnull().sum()
            if nan_count > 0:
                issues.append(f"⚠️ {nan_count} valeurs NaN dans {metric}")

# Vérification références
if ref_path.exists():
    if len(references) < 30:
        issues.append(f"⚠️ Seulement {len(references)}/30 références")

if issues:
    print("\n🔧 Corrections suggérées:")
    for issue in issues:
        print(f"   - {issue}")
else:
    print("✅ Aucun problème majeur détecté !")

print("\n" + "="*60)