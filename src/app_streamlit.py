import streamlit as st
import sys
import os
import time
import re
import base64

# Assurer l'accès aux modules du backend RAG
sys.path.insert(0, os.path.abspath('src'))
os.environ['HF_HUB_OFFLINE'] = '1'

from rag_agent import load_retriever, ask, LLM_MODEL, charger_tous_les_chunks, supprimer_accents
from recherche_exhaustive_ville import analyser_chunk
from langchain_community.llms import Ollama

# ==========================================
# CONFIGURATION ET DESIGN
# ==========================================
st.set_page_config(page_title="Copilot RAG - Microfinance", page_icon="💼", layout="wide")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_path = os.path.join("src", "hero_image.png")
banner_css = ""

if os.path.exists(img_path):
    img_base64 = get_base64_of_bin_file(img_path)
    banner_css = f"""
    .hero-banner {{
        background-image: linear-gradient(rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.7)), url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center 20%;
        padding: 80px 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }}
    .hero-title {{
        color: #FFFFFF;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }}
    .hero-subtitle {{
        color: #E2E8F0;
        font-size: 1.3rem;
        font-weight: 400;
    }}
    """
else:
    banner_css = """
    .hero-banner { background-color: #1E3A8A; padding: 60px 20px; border-radius: 12px; text-align: center; margin-bottom: 30px; }
    .hero-title { color: #FFFFFF; font-size: 3rem; font-weight: 800; margin-bottom: 10px; }
    .hero-subtitle { color: #CBD5E1; font-size: 1.2rem; }
    """

st.markdown(f"""
<style>
    .stApp {{ background-color: #F8FAFC; }}
    {banner_css}
    [data-testid="stMetric"] {{
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 15px 20px;
        border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 10px;
    }}
    [data-testid="stMetricLabel"] {{ color: #64748B !important; font-size: 0.95rem !important; font-weight: 500; }}
    [data-testid="stMetricValue"] {{ color: #1E3A8A !important; font-size: 1.8rem !important; font-weight: 700; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 20px; border-bottom: 1px solid #E2E8F0; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; background-color: transparent; padding-top: 10px; padding-bottom: 10px; color: #64748B; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 2px solid #1E3A8A; color: #1E3A8A !important; font-weight: 600; background-color: transparent; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# INITIALISATION BACKEND
# ==========================================
@st.cache_resource(show_spinner=False)
def setup_rag():
    retriever, vectorstore = load_retriever()
    llm = Ollama(model=LLM_MODEL, num_ctx=4096, temperature=0.0)
    _, tous_les_documents = charger_tous_les_chunks()
    return retriever, vectorstore, llm, tous_les_documents

st.markdown("""
<div class="hero-banner">
    <div class="hero-title">Assistant RAG Microfinance</div>
    <div class="hero-subtitle">Exploration intelligente de la base documentaire CEMAC via l'IA locale</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Connexion au moteur d'intelligence artificielle..."):
    retriever, vectorstore, llm, tous_les_documents = setup_rag()

# ==========================================
# CORPS DE L'APPLICATION
# ==========================================
# Noms d'onglets parfaitement professionnels
tab_chat, tab_ville = st.tabs(["💬 Assistant IA", "📍 Annuaire des EMF par Ville"])

# --- ONGLET 1 : CHAT RAG ---
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour. Je suis l'assistant IA spécialisé en microfinance (CEMAC). Comment puis-je vous aider aujourd'hui ?"}]

    with st.sidebar:
        st.write("### 📊 Indicateurs de Performance")
        st.caption("Suivi des métriques de la dernière requête.")
        st.write("")
        if "last_metrics" in st.session_state:
            m = st.session_state.last_metrics
            st.metric(label="Temps de réponse (s)", value=f"{m['temps_reponse']:.1f}")
            st.metric(label="Score de similarité", value=f"{m['score_similarite']:.3f}")
            st.metric(label="Nombre d'extraits lus", value=m['nb_documents'])
            st.write("")
            if m['statut'] == 'succes':
                st.success("✅ Réponse extraite avec succès.")
            else:
                st.info("ℹ️ Information indisponible dans la base.")
        else:
            st.info("Les indicateurs s'afficheront après votre première question.")

    for msg in st.session_state.messages:
        avatar = "💼" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
    if prompt := st.chat_input("Votre question (ex: Qu'est-ce que le microcrédit ?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user", avatar="👤").write(prompt)

        with st.chat_message("assistant", avatar="💼"):
            with st.spinner("Analyse documentaire en cours..."):
                resultat = ask(prompt, retriever, llm, vectorstore)
                reponse = resultat["reponse"]
                sources = resultat.get("sources", [])
                    "temps_reponse": resultat["temps_reponse"],
                    "score_similarite": resultat["score_similarite"],
                    "nb_documents": resultat["nb_documents"],
                    "statut": resultat["statut"]
                }
                st.write(reponse)
                
                if sources:
                    st.write("---")
# --- ONGLET 2 : ANNUAIRE DES VILLES ---
with tab_ville:
    st.write("#### Recherche d'Établissements de Microfinance (EMF)")
    st.caption("Consultez rapidement la liste des établissements enregistrés dans notre base de données géographique.")
    st.write("")
    
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        ville_recherche = st.text_input("Localisation", label_visibility="collapsed", placeholder="Saisissez une ville (ex: Douala, Maroua)...")
    with col_btn:
        lancer = st.button("Rechercher", use_container_width=True, type="primary")
    
    if lancer:
        if not ville_recherche:
            st.warning("Veuillez saisir une localisation.")
        else:
            with st.spinner(f"Recherche des établissements à '{ville_recherche}'..."):
                ville_normalisee = supprimer_accents(ville_recherche.lower())
                chunks_trouves = []
                for doc in tous_les_documents:
                    contenu_normalise = supprimer_accents(doc.page_content.lower())
                    motif = r"\b" + re.escape(ville_normalisee) + r"\b"
                    if re.search(motif, contenu_normalise):
                        lignes_loc, _ = analyser_chunk(doc.page_content, ville_normalisee)
                        if lignes_loc:
                            chunks_trouves.append(doc.page_content)

                if chunks_trouves:
                    st.success(f"✓ {len(chunks_trouves)} enregistrement(s) trouvé(s) pour la ville de '{ville_recherche}'.")
                    st.write("")
                    for i, chunk in enumerate(chunks_trouves, 1):
                        with st.expander(f"Détails - Résultat #{i}"):
                            st.code(chunk, language="text")
                else:
                    st.error(f"Aucun établissement EMF enregistré pour la localité de '{ville_recherche}'.")
