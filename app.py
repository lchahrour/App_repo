import streamlit as st

# MUST BE FIRST
st.set_page_config(
    page_title="Call Center Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- LAZY IMPORTS ---
# We don't import heavy stuff here to prevent startup hang
def get_pandas():
    import pandas as pd
    return pd

def get_plotly():
    import plotly.express as px
    import plotly.graph_objects as go
    return px, go

# --- APP START ---
st.title("📞 Call Center Performance Dashboard")

# Session State Initialization
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None

# Sidebar for Setup
with st.sidebar:
    st.header("⚙️ Configuration")
    sheet_url = st.text_input("URL Google Sheet", placeholder="https://docs.google.com/...")
    
    if sheet_url:
        if st.button("📂 Charger les données"):
            with st.spinner("Téléchargement en cours..."):
                from google_selector import list_sheets, choisir_feuille
                try:
                    fichier, sheets = list_sheets(sheet_url)
                    # For simplicity, we load the first sheet if not specified
                    df = choisir_feuille(fichier, sheets[0])
                    st.session_state.df_raw = df
                    st.success("Données chargées !")
                except Exception as e:
                    st.error(f"Erreur : {e}")

# Main Content
if st.session_state.df_raw is None:
    st.warning("👈 Veuillez configurer le Google Sheet dans la barre latérale pour commencer.")
    st.stop()

# If data is loaded, show the tabs
tab1, tab2, tab_ats = st.tabs(["📊 Analyse Globale", "🏢 Par Fournisseur", "📋 Analyse ATS"])

with tab1:
    st.header("Statistiques Globales")
    df = st.session_state.df_raw
    st.dataframe(df.head(100))

with tab2:
    st.header("Analyse Fournisseurs")
    if "list_name" in df.columns:
        px, go = get_plotly()
        fig = px.pie(df, names="list_name", title="Répartition par Fournisseur")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Colonne 'list_name' non trouvée.")

with tab_ats:
    st.header("Analyse ATS par IA")
    api_key = st.text_input("Clé API Gemini", type="password")
    if st.button("Lancer l'analyse ATS"):
        from ats_analysis import render_ats_tab
        render_ats_tab(api_key_input=api_key)