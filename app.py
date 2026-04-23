import streamlit as st

# AUCUN import lourd ici. On démarre à vide.
st.set_page_config(page_title="Debug Mode")

st.title("🚀 Mode Diagnostic Ultra-Léger")
st.write("Si vous voyez cette page, le serveur Streamlit est vivant !")

if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:
    if st.button("🔥 CHARGER L'APPLICATION COMPLÈTE"):
        st.session_state.started = True
        st.rerun()
else:
    with st.spinner("Chargement des modules lourds (Pandas, Plotly, IA)..."):
        import pandas as pd
        import plotly.express as px
        from google_selector import list_sheets, choisir_feuille
        from analyse import kpi_globaux
        from ats_analysis import render_ats_tab
        
        st.success("✅ Tout est chargé !")
        
        # Ici on remet le début de l'interface
        st.info("Utilisez la barre latérale pour configurer votre Google Sheet.")
        
        # On peut appeler les fonctions ici
        # (Je mets juste un aperçu pour tester)
        st.write("Base de données prête.")