import streamlit as st

# MUST BE FIRST LINE
st.set_page_config(
    page_title="Call Center Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import plotly.express as px
import json
import plotly.graph_objects as go

from google_selector import list_sheets, choisir_feuille
from ai_recommendation import GeminiAdvisor
from analyse import (
    kpi_globaux, appels_par_jour, appels_par_mois, appels_par_heure,
    repartition_classification, appels_par_fournisseur, classification_par_fournisseur,
    taux_remplissage_code_postal, comparer_codes_postaux, analyse_fiabilite_par_fournisseur,
    codes_postaux_non_correspondants, analyse_par_type_logement,
    comparer_types_logement, classification_detaillee_par_type, appels_par_piso_casa,
    analyse_par_type_logement
)
from ats_analysis import render_ats_tab

PALETTE = px.colors.qualitative.Set2
try:
    from google import genai
except Exception:
    genai = None

# Initialisation Session State
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None
if 'fichier' not in st.session_state:
    st.session_state.fichier = None
if 'sheets_list' not in st.session_state:
    st.session_state.sheets_list = None
if 'selected_sheets' not in st.session_state:
    st.session_state.selected_sheets = []

# SIDEBAR
with st.sidebar:
    st.title("📞 Call Center")
    st.markdown("---")
    st.subheader("🔗 Connexion Google Sheet")

    sheet_url = st.text_input("URL du Google Sheet", placeholder="https://docs.google.com/spreadsheets/d/...")

    if sheet_url:
        if st.button("📂 Charger les feuilles", type="primary"):
            try:
                with st.spinner("Chargement..."):
                    st.session_state.fichier, st.session_state.sheets_list = list_sheets(sheet_url)
                    st.success("Fichier trouvé !")
            except Exception as e:
                st.error(f"Erreur : {e}")

    if st.session_state.sheets_list:
        selected_sheets = st.multiselect(
            "Choisissez les feuilles",
            options=st.session_state.sheets_list,
            default=st.session_state.selected_sheets,
        )
        st.session_state.selected_sheets = selected_sheets

        if selected_sheets:
            if st.button("🔄 Charger les données", type="primary"):
                try:
                    all_dfs = []
                    for sheet_name in selected_sheets:
                        df = choisir_feuille(st.session_state.fichier, sheet_name)
                        if df is not None and not df.empty:
                            df['_source_feuille'] = sheet_name
                            all_dfs.append(df)
                    if all_dfs:
                        st.session_state.df_raw = pd.concat(all_dfs, ignore_index=True)
                        st.success("Données chargées !")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    api_key_input = st.text_input("🔑 Clé API Gemini", type="password")

# MAIN
if st.session_state.df_raw is None:
    st.info("👈 Commencez par entrer l'URL de votre Google Sheet dans la barre latérale")
    st.stop()

df = st.session_state.df_raw
tab1, tab2, tab_ats = st.tabs(["📊 Analyse globale", "🏢 Par fournisseur", "📋 Analyse ATS"])

with tab1:
    st.header("Analyse globale")
    kpis = kpi_globaux(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total appels", f"{kpis['total_appels']:,}")
    c2.metric("Appels utiles", kpis['appels_utiles'])
    c3.metric("Taux utiles", f"{kpis['taux_utiles_pct']}%")
    st.divider()
    df_jour = appels_par_jour(df)
    if not df_jour.empty:
        st.plotly_chart(px.bar(df_jour, x="date", y="nb_appels"), use_container_width=True)

with tab2:
    st.header("Par fournisseur")
    df_f = appels_par_fournisseur(df)
    if not df_f.empty:
        st.dataframe(df_f, use_container_width=True)

with tab_ats:
    render_ats_tab(api_key_input=api_key_input)