@echo off
chcp 65001 > nul
title Téléchargement Ollama - Reprise Automatique

echo ============================================================
echo 📥 TÉLÉCHARGEMENT OLLAMA AVEC REPRISE AUTOMATIQUE
echo ============================================================
echo.
echo Modèle : phi3:3.8b-mini-4k-instruct-q4_K_M
echo Taille : 2.4 Go
echo.
echo 🔄 Le script attendra que la connexion soit rétablie
echo 📊 La progression sera automatiquement reprise
echo.
echo ============================================================
echo.

:loop
echo [%date% %time%] Lancement du téléchargement...
ollama pull phi3:3.8b-mini-4k-instruct-q4_K_M

if errorlevel 1 (
    echo.
    echo ⚠️ Connexion perdue à [%time%]
    echo 🔄 Attente de la connexion...
    echo 📌 Change ta SIM quand tu es prêt.
    echo.
    echo Appuie sur une touche quand la connexion est rétablie...
    pause > nul
    goto loop
)

echo.
echo ============================================================
echo ✅ TÉLÉCHARGEMENT TERMINÉ AVEC SUCCÈS !
echo ============================================================
pause