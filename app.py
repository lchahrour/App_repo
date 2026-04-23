import streamlit as st
import sys
import subprocess
import os


# --- REAL APP START ---
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
except Exception as e:
    st.error(f"Erreur fatale au chargement des librairies: {e}")
    st.stop()

st.set_page_config(
    page_title="Call Center Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Debug info (hidden in expander)
with st.expander("🔍 System Info", expanded=False):
    st.write(f"Python Version: {sys.version}")
    st.write(f"Venv: {sys.prefix}")

from google_selector import list_sheets, choisir_feuille
from ai_recommendation import GeminiAdvisor
from analyse import (
    kpi_globaux, appels_par_jour, appels_par_mois, appels_par_heure,
    repartition_classification, appels_par_fournisseur, classification_par_fournisseur
)
from ats_analysis import render_ats_tab

# --- THEMES AND STATE ---
PALETTE = px.colors.qualitative.Set2
if 'df_raw' not in st.session_state: st.session_state.df_raw = None
if 'fichier' not in st.session_state: st.session_state.fichier = None
if 'sheets_list' not in st.session_state: st.session_state.sheets_list = None
if 'selected_sheets' not in st.session_state: st.session_state.selected_sheets = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("📞 Call Center Dashboard")
    st.markdown("---")
    sheet_url = st.text_input("URL Google Sheet", placeholder="https://docs.google.com/...")
    
    if sheet_url:
        if st.button("📂 Charger les feuilles", type="primary"):
            try:
                with st.spinner("Téléchargement..."):
                    st.session_state.fichier, st.session_state.sheets_list = list_sheets(sheet_url)
                    st.success("Fichier connecté !")
            except Exception as e:
                st.error(f"Erreur : {e}")

    if st.session_state.sheets_list:
        selected = st.multiselect("Feuilles", st.session_state.sheets_list, default=st.session_state.selected_sheets)
        st.session_state.selected_sheets = selected
        if selected and st.button("🔄 Actualiser les données"):
            try:
                all_dfs = [choisir_feuille(st.session_state.fichier, s) for s in selected]
                st.session_state.df_raw = pd.concat([d for d in all_dfs if d is not None], ignore_index=True)
            except Exception as e:
                st.error(f"Erreur : {e}")

    api_key_input = st.text_input("🔑 API Gemini", type="password")

# --- MAIN INTERFACE ---
if st.session_state.df_raw is None:
    st.info("👈 Connectez un Google Sheet dans la barre latérale pour afficher les analyses.")
    st.stop()

df = st.session_state.df_raw
tab1, tab2, tab_ats = st.tabs(["📊 Global", "🏢 Fournisseurs", "📋 ATS"])

with tab1:
    kpis = kpi_globaux(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total appels", f"{len(df):,}")
    c2.metric("Taux utiles", f"{kpis.get('taux_utiles_pct', 'N/A')}%")
    c3.metric("Durée Moyenne", f"{kpis.get('duree_moyenne_sec', 0):.0f}s")
    st.plotly_chart(px.bar(appels_par_jour(df), x="date", y="nb_appels", title="Appels par jour"), use_container_width=True)

with tab2:
    st.header("Analyse Fournisseurs")
    st.dataframe(appels_par_fournisseur(df), use_container_width=True)

with tab_ats:
    render_ats_tab(api_key_input=api_key_input)