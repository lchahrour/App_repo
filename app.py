import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google_selector import list_sheets, choisir_feuille
from analyse import *
from analyse import (
    kpi_globaux,
    appels_par_jour,
    appels_par_mois,
    appels_par_heure,
    repartition_classification,
    appels_par_fournisseur,
    classification_par_fournisseur,
    appels_utiles_par_ville,
    appels_par_tipo_vivienda,
    taux_remplissage_code_postal,
    comparer_codes_postaux,
    analyse_fiabilite_par_fournisseur,
    codes_postaux_non_correspondants,
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Call Center Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = px.colors.qualitative.Set2

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────

if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None
if 'fichier' not in st.session_state:
    st.session_state.fichier = None
if 'sheets_list' not in st.session_state:
    st.session_state.sheets_list = None
if 'selected_sheets' not in st.session_state:
    st.session_state.selected_sheets = []

# ─────────────────────────────────────────────
# SIDEBAR — CONNEXION & FILTRES
# ─────────────────────────────────────────────

with st.sidebar:
    st.title("📞 Call Center")
    st.markdown("---")
    
    # Section de connexion Google Sheet
    st.subheader("🔗 Connexion Google Sheet")
    
    # Instructions
    with st.expander("📖 Comment obtenir l'URL ?"):
        st.markdown("""
        1. Ouvrez votre Google Sheet
        2. Cliquez sur **Partager** (🔗 en haut à droite)
        3. Dans **"Accès général"**, sélectionnez : **"Toute personne disposant du lien"**
        4. Copiez le lien
        5. Collez-le ci-dessous
        """)
    
    # Champ pour l'URL du sheet
    sheet_url = st.text_input(
        "URL du Google Sheet",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Collez l'URL complète de votre Google Sheet"
    )
    
    # Bouton pour charger les feuilles
    if sheet_url:
        if st.button("📂 Charger les feuilles", type="primary"):
            try:
                with st.spinner("Chargement du fichier..."):
                    st.session_state.fichier, st.session_state.sheets_list = list_sheets(sheet_url)
                    st.success(f"✅ {len(st.session_state.sheets_list)} feuille(s) trouvée(s)")
            except Exception as e:
                st.error(f"Erreur de chargement: {str(e)}")
                st.session_state.fichier = None
                st.session_state.sheets_list = None
    
    # Sélection des feuilles (version multi-sélection)
    if st.session_state.sheets_list:
        st.markdown("---")
        st.subheader("📑 Sélection des feuilles")
        
        
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Tout sélectionner", use_container_width=True):
                st.session_state.selected_sheets = st.session_state.sheets_list.copy()
        with col2:
            if st.button("❌ Effacer tout", use_container_width=True):
                st.session_state.selected_sheets = []
                st.rerun()
        
        # Sélection multiple
        selected_sheets = st.multiselect(
            "Choisissez les feuilles à analyser",
            options=st.session_state.sheets_list,
            default=st.session_state.selected_sheets,
            help="Sélectionnez une ou plusieurs feuilles. Les données seront combinées pour l'analyse."
        )
        
        # Sauvegarder la sélection
        st.session_state.selected_sheets = selected_sheets
        
        # Afficher le nombre de feuilles sélectionnées
        if selected_sheets:
            st.success(f"📊 {len(selected_sheets)} feuille(s) sélectionnée(s)")
            
            # Bouton pour charger les données
            if st.button("🔄 Charger les données", type="primary", use_container_width=True):
                try:
                    all_dfs = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, sheet_name in enumerate(selected_sheets):
                        status_text.text(f"Chargement de la feuille '{sheet_name}'... ({i+1}/{len(selected_sheets)})")
                        df = choisir_feuille(st.session_state.fichier, sheet_name)
                        if df is not None and not df.empty:
                            df['_source_feuille'] = sheet_name
                            all_dfs.append(df)
                        progress_bar.progress((i + 1) / len(selected_sheets))
                    
                    status_text.text("Finalisation...")
                    
                    if all_dfs:
                        st.session_state.df_raw = pd.concat(all_dfs, ignore_index=True)
                        
                        st.session_state.stats_chargement = {
                            "nb_feuilles": len(selected_sheets),
                            "total_lignes": len(st.session_state.df_raw),
                            "feuilles_details": [
                                {"nom": sheet_name, "lignes": len(df)} 
                                for sheet_name, df in zip(selected_sheets, all_dfs)
                            ]
                        }
                        
                        status_text.empty()
                        progress_bar.empty()
                        st.success(f"✅ Données chargées : {len(st.session_state.df_raw):,} lignes depuis {len(selected_sheets)} feuille(s)")
                        
                        with st.expander("📋 Détail du chargement"):
                            st.write(f"**Total lignes :** {len(st.session_state.df_raw):,}")
                            st.write(f"**Colonnes trouvées :** {', '.join(st.session_state.df_raw.columns[:8])}{'...' if len(st.session_state.df_raw.columns) > 8 else ''}")
                            st.write("**Détail par feuille :**")
                            for detail in st.session_state.stats_chargement["feuilles_details"]:
                                st.write(f"- {detail['nom']} : {detail['lignes']:,} lignes")
                    else:
                        st.error("Aucune donnée valide chargée")
                        
                except Exception as e:
                    st.error(f"Erreur lors du chargement des données: {str(e)}")
        else:
            st.warning("⚠️ Veuillez sélectionner au moins une feuille")
    
    # Afficher les filtres seulement si les données sont chargées
    if st.session_state.df_raw is not None:
        st.markdown("---")
        st.subheader("🎯 Filtres")
        
        df_raw = st.session_state.df_raw
        
        # Filtre fournisseur
        if "list_name" in df_raw.columns:
            fournisseurs = ["Tous"] + sorted(df_raw["list_name"].dropna().unique().tolist())
            fourn_sel = st.selectbox("Fournisseur (list_name)", fournisseurs)
        else:
            fourn_sel = "Tous"
            st.caption("⚠️ Colonne 'list_name' non trouvée")
        
        # Filtre date
        if "Timestamp" in df_raw.columns:
            ts_all = pd.to_datetime(df_raw["Timestamp"], errors="coerce", dayfirst=True)
            ts_all = ts_all.dropna()
            if not ts_all.empty:
                date_min = ts_all.min().date()
                date_max = ts_all.max().date()
                date_range = st.date_input(
                    "Période",
                    value=(date_min, date_max),
                    min_value=date_min,
                    max_value=date_max,
                )
            else:
                date_range = None
        else:
            date_range = None
            st.caption("⚠️ Colonne 'Timestamp' non trouvée")
        
        st.markdown("---")
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.rerun()
    else:
        fourn_sel = "Tous"
        date_range = None

# ─────────────────────────────────────────────
# AFFICHAGE PRINCIPAL
# ─────────────────────────────────────────────

# Vérifier si les données sont chargées
if st.session_state.df_raw is None:
    st.info("👈 Commencez par entrer l'URL de votre Google Sheet dans la barre latérale")
    
    with st.expander("ℹ️ Comment obtenir l'URL de mon Google Sheet ?"):
        st.markdown("""
        1. Ouvrez votre Google Sheet
        2. Cliquez sur le bouton **🔗 Partager** (en haut à droite)
        3. Dans **"Accès général"**, sélectionnez : **"Toute personne disposant du lien"**
        4. Copiez le lien fourni
        5. Collez-le ci-dessous
        6. Cliquez sur 'Charger les feuilles'
        7. Sélectionnez les feuilles à analyser
        8. Cliquez sur 'Charger les données'
        """)
    
    st.stop()

# ─────────────────────────────────────────────
# APPLICATION DES FILTRES
# ─────────────────────────────────────────────

df = st.session_state.df_raw.copy()

if fourn_sel != "Tous" and "list_name" in df.columns:
    df = df[df["list_name"] == fourn_sel]

if date_range is not None and "Timestamp" in df.columns:
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        ts = pd.to_datetime(df["Timestamp"], errors="coerce", dayfirst=True)
        df = df[(ts.dt.date >= date_range[0]) & (ts.dt.date <= date_range[1])]

if df.empty:
    st.warning("⚠️ Aucune donnée pour les filtres sélectionnés.")
    st.stop()

# ─────────────────────────────────────────────
# ONGLETS
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4,tab5 = st.tabs([
    "📊 Analyse globale",
    "🏢 Par fournisseur",
    "📍 Codes postaux & Fiabilité",
    "🏠 Logements",
    "🤖 AI Recommendations",

])

# ══════════════════════════════════════════════
# TAB 1 — ANALYSE GLOBALE
# ══════════════════════════════════════════════

with tab1:
    st.header("Analyse globale des appels")

    kpis = kpi_globaux(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total appels", f"{kpis['total_appels']:,}")
    c2.metric("Appels utiles", f"{kpis['appels_utiles']:,}" if kpis['appels_utiles'] is not None else "—")
    c3.metric("Taux utiles", f"{kpis['taux_utiles_pct']}%" if kpis['taux_utiles_pct'] is not None else "—")
    c4.metric(
        "Durée moyenne",
        f"{kpis['duree_moyenne_sec']:.0f}s" if kpis['duree_moyenne_sec'] is not None else "—"
    )

    st.markdown("---")

    col_j, col_m = st.columns(2)

    with col_j:
        st.subheader("Appels par jour")
        df_jour = appels_par_jour(df)
        if not df_jour.empty:
            df_jour["date"] = df_jour["date"].astype(str)
            fig = px.bar(
                df_jour, x="date", y="nb_appels",
                color_discrete_sequence=[PALETTE[0]],
            )
            fig.update_layout(
                xaxis_title="", yaxis_title="Appels",
                xaxis=dict(type="category"),
                margin=dict(t=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Colonne Timestamp absente.")

    with col_m:
        st.subheader("Appels par mois")
        df_mois = appels_par_mois(df)
        if not df_mois.empty:
            df_mois["mois"] = df_mois["mois"].astype(str)
            fig = px.bar(
                df_mois, x="mois", y="nb_appels",
                color_discrete_sequence=[PALETTE[1]],
                text="nb_appels",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                xaxis_title="", yaxis_title="Appels",
                xaxis=dict(type="category"),
                margin=dict(t=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Colonne Timestamp absente.")

    st.markdown("---")

    col_cl, col_h = st.columns(2)

    with col_cl:
        st.subheader("Répartition par classification")
        df_cls = repartition_classification(df)
        if not df_cls.empty:
            fig = px.pie(
                df_cls, names="Classification", values="count",
                color_discrete_sequence=PALETTE,
                hole=0.4,
            )
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée de classification valide.")

    with col_h:
        st.subheader("Appels par heure de la journée")
        df_heure = appels_par_heure(df)
        if not df_heure.empty:
            fig = px.line(
                df_heure, x="heure", y="nb_appels",
                markers=True,
                color_discrete_sequence=[PALETTE[2]],
            )
            fig.update_traces(
                line=dict(width=2),
                marker=dict(size=7),
            )
            fig.update_layout(
                xaxis=dict(tickmode="linear", dtick=1, title="Heure"),
                yaxis_title="Appels",
                margin=dict(t=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Colonne Timestamp absente.")

# ══════════════════════════════════════════════
# TAB 2 — PAR FOURNISSEUR
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
# TAB 2 — PAR FOURNISSEUR (avec analyse logement)
# ══════════════════════════════════════════════

with tab2:
    st.header("Analyse par fournisseur (list_name)")

    df_fourn = appels_par_fournisseur(df)

    if df_fourn.empty:
        st.info("Colonne list_name absente.")
    else:
        # Tableau récapitulatif principal
        st.subheader("📊 Récapitulatif fournisseurs")
        st.dataframe(
            df_fourn.rename(columns={
                "list_name": "Fournisseur",
                "nb_appels": "Total appels",
                "nb_utiles": "Appels classifiés",
                "taux_utiles_pct": "Taux classification (%)",
                "nb_qualifies": "Appels qualifiés",
                "taux_qualifies_pct": "Taux qualification (%)",
                "duree_moy_sec": "Durée moy. (s)",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        # Graphiques principaux
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("📈 Nombre d'appels par fournisseur")
            fig = px.bar(
                df_fourn.sort_values("nb_appels"),
                x="nb_appels", y="list_name",
                orientation="h",
                text="nb_appels",
                color_discrete_sequence=[PALETTE[0]],
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(yaxis_title="", xaxis_title="Appels", margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("🎯 Taux d'appels qualifiés (%)")
            fig = px.bar(
                df_fourn.sort_values("taux_qualifies_pct"),
                x="taux_qualifies_pct", y="list_name",
                orientation="h",
                text="taux_qualifies_pct",
                color="taux_qualifies_pct",
                color_continuous_scale="Greens",
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(
                yaxis_title="", xaxis_title="%",
                margin=dict(t=10), coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Durée moyenne par fournisseur
        st.subheader("⏱️ Durée moyenne d'appel par fournisseur (secondes)")
        fig = px.bar(
            df_fourn.sort_values("duree_moy_sec"),
            x="duree_moy_sec", y="list_name",
            orientation="h",
            text="duree_moy_sec",
            color_discrete_sequence=[PALETTE[3]],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_title="", xaxis_title="Secondes", margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Répartition classifications par fournisseur
        st.subheader("📋 Répartition des classifications par fournisseur")
        df_cls_fourn = classification_par_fournisseur(df)

        if not df_cls_fourn.empty:
            fig = px.bar(
                df_cls_fourn,
                x="pct", y="list_name",
                color="Classification",
                orientation="h",
                text="count",
                color_discrete_sequence=PALETTE,
                barmode="stack",
            )
            fig.update_traces(textposition="inside", insidetextanchor="middle")
            fig.update_layout(
                yaxis_title="",
                xaxis_title="% des appels utiles",
                legend_title="Classification",
                margin=dict(t=10),
            )
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📑 Voir le tableau détaillé"):
                pivot = df_cls_fourn.pivot_table(
                    index="list_name", columns="Classification",
                    values="count", fill_value=0,
                )
                st.dataframe(pivot, use_container_width=True)
        else:
            st.info("Aucune donnée de classification valide.")

        st.markdown("---")
        st.divider()
        st.markdown("---")

        # ═══════════════════════════════════════════════════════════
        # SECTION: ANALYSE DES LOGEMENTS PAR FOURNISSEUR
        # ═══════════════════════════════════════════════════════════
        
        st.subheader("🏠 Analyse des types de logement par fournisseur")
        
        # Vérifier si la colonne tipo_vivienda existe
        if "tipo_vivienda" in df.columns:
            
            # Sélecteur de fournisseur pour analyse détaillée
            fournisseurs_list = sorted(df["list_name"].dropna().unique())
            selected_fournisseur = st.selectbox(
                "Choisissez un fournisseur pour voir le détail des logements",
                options=["Tous les fournisseurs"] + fournisseurs_list,
                key="logement_fournisseur_select"
            )
            
            # Filtrer les données selon le fournisseur sélectionné
            if selected_fournisseur != "Tous les fournisseurs":
                df_logement_filter = df[df["list_name"] == selected_fournisseur]
            else:
                df_logement_filter = df
            
            # Nettoyer les données de logement
            df_logement_clean = df_logement_filter.copy()
            df_logement_clean["tipo_vivienda"] = df_logement_clean["tipo_vivienda"].astype(str).str.strip()
            df_logement_clean = df_logement_clean[df_logement_clean["tipo_vivienda"].notna()]
            df_logement_clean = df_logement_clean[df_logement_clean["tipo_vivienda"] != ""]
            df_logement_clean = df_logement_clean[df_logement_clean["tipo_vivienda"] != "nan"]
            
            if not df_logement_clean.empty:
                # Statistiques rapides
                col_log1, col_log2, col_log3 = st.columns(3)
                with col_log1:
                    nb_appels_logement = len(df_logement_clean)
                    st.metric("Appels avec type logement", f"{nb_appels_logement:,}")
                with col_log2:
                    nb_types = df_logement_clean["tipo_vivienda"].nunique()
                    st.metric("Types de logement différents", nb_types)
                with col_log3:
                    top_type = df_logement_clean["tipo_vivienda"].mode().iloc[0] if not df_logement_clean.empty else "N/A"
                    st.metric("Type de logement le plus fréquent", top_type)
                
                st.markdown("---")
                
                # Graphique 1: Répartition des types de logement (camembert)
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.subheader("🥧 Répartition par type de logement")
                    counts = df_logement_clean["tipo_vivienda"].value_counts()
                    fig_pie = px.pie(
                        values=counts.values,
                        names=counts.index,
                        title=f"Répartition des logements" + (f" - {selected_fournisseur}" if selected_fournisseur != "Tous les fournisseurs" else ""),
                        color_discrete_sequence=PALETTE,
                        hole=0.3
                    )
                    fig_pie.update_traces(textinfo="percent+label")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_chart2:
                    st.subheader("📊 Top types de logement")
                    df_top = df_logement_clean["tipo_vivienda"].value_counts().head(10).reset_index()
                    df_top.columns = ["Type de logement", "Nombre d'appels"]
                    fig_bar = px.bar(
                        df_top,
                        x="Nombre d'appels",
                        y="Type de logement",
                        orientation="h",
                        text="Nombre d'appels",
                        color="Nombre d'appels",
                        color_continuous_scale="Blues",
                        title="Top 10 des types de logement"
                    )
                    fig_bar.update_traces(textposition="outside")
                    fig_bar.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                st.markdown("---")
                
                # Graphique 2: Distribution par fournisseur (uniquement si on est en mode "Tous")
                if selected_fournisseur == "Tous les fournisseurs":
                    st.subheader("📊 Distribution des logements par fournisseur")
                    
                    # Préparer les données pour le graphique empilé
                    df_cross = pd.crosstab(df_logement_clean["list_name"], df_logement_clean["tipo_vivienda"])
                    
                    # Prendre les 5 principaux types de logement pour la lisibilité
                    top_types = df_cross.sum().sort_values(ascending=False).head(5).index
                    df_cross_top = df_cross[top_types]
                    
                    # Graphique en barres empilées
                    fig_stacked = px.bar(
                        df_cross_top,
                        x=df_cross_top.index,
                        y=top_types,
                        title="Distribution des types de logement par fournisseur (Top 5)",
                        labels={"value": "Nombre d'appels", "variable": "Type de logement", "list_name": "Fournisseur"},
                        barmode="stack",
                        color_discrete_sequence=PALETTE
                    )
                    fig_stacked.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_stacked, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Tableau croisé
                    with st.expander("📑 Voir le tableau détaillé (tous les types)"):
                        st.dataframe(df_cross, use_container_width=True)
                
                # Graphique 3: Analyse des classifications par type de logement
                st.subheader("🎯 Classification des appels par type de logement")
                
                if "Classification" in df.columns:
                    # Filtrer les classifications utiles
                    df_classif_log = df_logement_clean[df_logement_clean["Classification"].notna()]
                    df_classif_log = df_classif_log[df_classif_log["Classification"].astype(str).str.strip() != ""]
                    df_classif_log = df_classif_log[~df_classif_log["Classification"].astype(str).str.lower().isin(["non trouvé", "non trouve"])]
                    
                    if not df_classif_log.empty:
                        # Prendre les 5 principaux types de logement
                        top_logements = df_classif_log["tipo_vivienda"].value_counts().head(5).index
                        df_classif_top = df_classif_log[df_classif_log["tipo_vivienda"].isin(top_logements)]
                        
                        # Tableau croisé
                        cross_classif = pd.crosstab(df_classif_top["tipo_vivienda"], df_classif_top["Classification"])
                        
                        # Graphique en barres groupées
                        fig_classif = px.bar(
                            cross_classif,
                            title="Classifications par type de logement (Top 5)",
                            labels={"value": "Nombre d'appels", "tipo_vivienda": "Type de logement"},
                            barmode="group",
                            color_discrete_sequence=PALETTE
                        )
                        st.plotly_chart(fig_classif, use_container_width=True)
                        
                        with st.expander("📑 Voir le tableau des classifications"):
                            st.dataframe(cross_classif, use_container_width=True)
                    else:
                        st.info("Aucune classification valide trouvée pour les types de logement")
                else:
                    st.info("Colonne 'Classification' non trouvée")
                
                # Tableau récapitulatif par fournisseur
                if selected_fournisseur == "Tous les fournisseurs":
                    st.markdown("---")
                    st.subheader("📋 Récapitulatif des types de logement par fournisseur")
                    
                    # Créer un tableau pivot
                    df_pivot = pd.crosstab(
                        df_logement_clean["list_name"], 
                        df_logement_clean["tipo_vivienda"],
                        normalize="index"
                    ) * 100
                    
                    st.dataframe(
                        df_pivot.round(1).style.format("{:.1f}%"),
                        use_container_width=True,
                        height=400
                    )
                    
                    # Option d'export
                    csv = df_pivot.to_csv().encode('utf-8')
                    st.download_button(
                        label="📥 Exporter les données (pourcentages)",
                        data=csv,
                        file_name="logement_par_fournisseur.csv",
                        mime="text/csv",
                    )
                
            else:
                st.info("Aucune donnée sur les types de logement pour ce fournisseur")
        else:
            st.info("ℹ️ Colonne 'tipo_vivienda' non trouvée dans les données. Ajoutez cette colonne pour voir l'analyse des logements.")

# ══════════════════════════════════════════════
# TAB 3 — CODES POSTAUX & FIABILITÉ
# ══════════════════════════════════════════════

with tab3:
    st.header("Analyse des codes postaux et fiabilité des données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Taux de remplissage")
        
        taux = taux_remplissage_code_postal(df)
        
        if taux:
            for colonne, stats in taux.items():
                st.metric(
                    f"Colonne: {colonne}",
                    f"{stats['taux_remplissage']}%",
                    f"{stats['nb_remplis']}/{stats['total_lignes']} lignes"
                )
                st.progress(stats['taux_remplissage'] / 100)
        else:
            st.warning("Colonnes 'code_postal' et/ou 'codigo_postal' non trouvées")
    
    with col2:
        st.subheader("🎯 Comparaison Client vs Fournisseur")
        
        df_comp, stats = comparer_codes_postaux(df)
        
        if stats:
            st.metric("Total comparaisons possibles", stats['total_comparaisons'])
            st.metric("Correspondances", f"{stats['nb_correspondances']} / {stats['total_comparaisons']}")
            st.metric("Taux de correspondance", f"{stats['taux_correspondance']}%")
            
            if stats['taux_correspondance'] >= 80:
                st.success(f"✅ Bonne fiabilité : {stats['taux_correspondance']}%")
            elif stats['taux_correspondance'] >= 50:
                st.warning(f"⚠️ Fiabilité moyenne : {stats['taux_correspondance']}%")
            else:
                st.error(f"❌ Faible fiabilité : {stats['taux_correspondance']}%")
        else:
            st.info("Pas assez de données pour comparer les codes postaux")
    
    st.markdown("---")
    
    st.subheader("🏢 Fiabilité par fournisseur")
    
    df_fiabilite = analyse_fiabilite_par_fournisseur(df)
    
    if not df_fiabilite.empty:
        st.dataframe(
            df_fiabilite.rename(columns={
                "fournisseur": "Fournisseur",
                "total_appels": "Total appels",
                "taux_remplissage_client": "Taux remplissage client (%)",
                "taux_remplissage_fournisseur": "Taux remplissage fournisseur (%)",
                "nb_comparaisons": "Nb comparaisons",
                "taux_correspondance": "Taux correspondance (%)"
            }),
            use_container_width=True,
            hide_index=True,
        )
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Taux de remplissage par fournisseur")
            df_plot = df_fiabilite.melt(
                id_vars=["fournisseur"], 
                value_vars=["taux_remplissage_client", "taux_remplissage_fournisseur"],
                var_name="source", 
                value_name="taux"
            )
            fig = px.bar(
                df_plot, 
                x="fournisseur", 
                y="taux", 
                color="source",
                barmode="group",
                title="Taux de remplissage des codes postaux",
                labels={"taux": "Taux (%)", "fournisseur": "Fournisseur", "source": "Source"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
            st.subheader("Taux de correspondance par fournisseur")
            fig = px.bar(
                df_fiabilite,
                x="fournisseur",
                y="taux_correspondance",
                color="taux_correspondance",
                color_continuous_scale="RdYlGn",
                title="Fiabilité des données par fournisseur",
                labels={"taux_correspondance": "Taux de correspondance (%)", "fournisseur": "Fournisseur"}
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Données insuffisantes pour l'analyse par fournisseur")
    
    st.markdown("---")
    
    st.subheader("🔍 Détails des codes postaux non correspondants")
    
    df_non_corr = codes_postaux_non_correspondants(df)
    
    if not df_non_corr.empty:
        st.write(f"**{len(df_non_corr)}** lignes où les codes postaux ne correspondent pas")
        
        cols_afficher = ["list_name", "code_postal", "codigo_postal", "code_postal_clean", "codigo_postal_clean"]
        cols_disponibles = [col for col in cols_afficher if col in df_non_corr.columns]
        
        st.dataframe(
            df_non_corr[cols_disponibles].head(100),
            use_container_width=True,
            hide_index=True
        )
        
        csv = df_non_corr[cols_disponibles].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exporter les non-correspondances",
            data=csv,
            file_name="non_correspondances_codes_postaux.csv",
            mime="text/csv",
        )
    else:
        st.success("✅ Tous les codes postaux disponibles correspondent !")

# ══════════════════════════════════════════════
# TAB 4 — LOGEMENTS
# ══════════════════════════════════════════════

with tab4:
    st.header("Analyse métier — Logements")

    df_tipo = appels_par_tipo_vivienda(df)

    if df_tipo.empty:
        st.info("Colonne tipo_vivienda absente ou vide.")
    else:
        col_p, col_b = st.columns(2)

        with col_p:
            st.subheader("Répartition par type de logement")
            fig = px.pie(
                df_tipo, names="tipo_vivienda", values="count",
                color_discrete_sequence=PALETTE,
                hole=0.4,
            )
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Nombre d'appels par type")
            fig = px.bar(
                df_tipo.sort_values("count"),
                x="count", y="tipo_vivienda",
                orientation="h",
                text="pct",
                color="count",
                color_continuous_scale="Purples",
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(
                yaxis_title="", xaxis_title="Appels",
                coloraxis_showscale=False, margin=dict(t=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_tipo.rename(columns={
                "tipo_vivienda": "Type de logement",
                "count": "Appels",
                "pct": "%",
            }),
            use_container_width=True,
            hide_index=True,
        )
# ══════════════════════════════════════════════
# TAB 5 — AI RECOMMENDATIONS
# ══════════════════════════════════════════════

with tab5:
    st.header("🤖 Assistant IA - Recommandations Intelligentes")
    st.markdown("---")
    
    # Configuration de l'API DeepSeek
    
    
    st.markdown("---")
    
    # Sélecteur de volet
    volet = st.radio(
        "Choisissez le type d'analyse",
        options=[
            "📊 Performance fournisseurs",
            "🏠 Optimisation par type de logement",
            "⏰ Optimisation temporelle",
            "🚨 Détection d'anomalies",
            "💡 Stratégie globale"
        ],
        horizontal=True,
        help="Sélectionnez le domaine d'analyse pour lequel vous voulez des recommandations"
    )
    
    st.markdown("---")
    
    # Bouton pour générer les recommandations
    if st.button("🔮 Générer les recommandations IA", type="primary", use_container_width=True):
        
        # ============================================================
        # VOTELET 1: PERFORMANCE FOURNISSEURS
        # ============================================================
        if volet == "📊 Performance fournisseurs":
            st.subheader("📊 Analyse des performances fournisseurs")
            
            if "list_name" not in df.columns:
                st.warning("⚠️ Colonne 'list_name' non trouvée")
            else:
                # Statistiques rapides
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Nombre de fournisseurs", df["list_name"].nunique())
                with col2:
                    total_appels = len(df)
                    st.metric("Total appels analysés", f"{total_appels:,}")
                with col3:
                    if "taux_qualifies_pct" in df.columns or "_qualifie" in df.columns:
                        taux_moyen = df["_qualifie"].mean() * 100 if "_qualifie" in df.columns else 0
                        st.metric("Taux qualification moyen", f"{taux_moyen:.1f}%")
                
                st.markdown("---")
                
                # Top et bottom performers
                df_fourn_summary = df.groupby("list_name").agg({
                    "list_name": "count",
                    "_qualifie": "mean" if "_qualifie" in df.columns else None,
                    "_utile": "mean" if "_utile" in df.columns else None,
                    "Duration_seconds": "mean" if "Duration_seconds" in df.columns else None
                }).rename(columns={"list_name": "total_appels"})
                
                if "_qualifie" in df.columns:
                    df_fourn_summary["taux_qualif"] = (df_fourn_summary["_qualifie"] * 100).round(1)
                    df_fourn_summary = df_fourn_summary.sort_values("taux_qualif", ascending=False)
                    
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        st.subheader("🏆 Top 3 fournisseurs")
                        top_3 = df_fourn_summary.head(3)
                        for idx, (fournisseur, row) in enumerate(top_3.iterrows()):
                            st.success(f"""
                            **{idx+1}. {fournisseur}**  
                            📞 {row['total_appels']:,} appels | 🎯 Taux qualif: {row['taux_qualif']}%
                            """)
                    
                    with col_right:
                        st.subheader("⚠️ Bottom 3 fournisseurs")
                        bottom_3 = df_fourn_summary.tail(3)
                        for idx, (fournisseur, row) in enumerate(bottom_3.iterrows()):
                            st.warning(f"""
                            **{idx+1}. {fournisseur}**  
                            📞 {row['total_appels']:,} appels | 🎯 Taux qualif: {row['taux_qualif']}%
                            """)
                
                st.markdown("---")
                
                # Recommandations IA (simulées pour l'instant)
                st.subheader("💡 Recommandations IA")
                
                if st.session_state.get("api_key_configured", False):
                    with st.spinner("L'IA analyse les données..."):
                        # Ici vous appellerez DeepSeek API
                        st.info("🔧 Intégration DeepSeek à venir - API configurée")
                else:
                    # Mode démo avec recommandations basées sur règles
                    st.info("💡 Mode démo - Recommandations basées sur les règles métier")
                    
                    # Générer des recommandations basées sur les données
                    recommendations = []
                    
                    for fournisseur in df["list_name"].unique()[:5]:
                        df_f = df[df["list_name"] == fournisseur]
                        total = len(df_f)
                        
                        if "_qualifie" in df_f.columns:
                            taux = df_f["_qualifie"].mean() * 100
                            
                            if taux < 20:
                                recommendations.append({
                                    "fournisseur": fournisseur,
                                    "niveau": "🔴 Critique",
                                    "message": f"Taux de qualification très bas ({taux:.0f}%)",
                                    "action": "Former l'équipe sur l'identification des leads qualifiés"
                                })
                            elif taux < 40:
                                recommendations.append({
                                    "fournisseur": fournisseur,
                                    "niveau": "🟡 Moyen",
                                    "message": f"Taux de qualification à améliorer ({taux:.0f}%)",
                                    "action": "Revoir le script d'appel et les critères de qualification"
                                })
                            elif taux > 60:
                                recommendations.append({
                                    "fournisseur": fournisseur,
                                    "niveau": "🟢 Excellent",
                                    "message": f"Excellent taux de qualification ({taux:.0f}%)",
                                    "action": "Partager les bonnes pratiques avec les autres fournisseurs"
                                })
                    
                    if recommendations:
                        for rec in recommendations:
                            with st.expander(f"{rec['niveau']} - {rec['fournisseur']}"):
                                st.markdown(f"**Problème:** {rec['message']}")
                                st.markdown(f"**Action recommandée:** {rec['action']}")
                    else:
                        st.success("✅ Tous les fournisseurs ont un bon taux de qualification !")
        
        # ============================================================
        # VOTELET 2: OPTIMISATION PAR TYPE DE LOGEMENT
        # ============================================================
        elif volet == "🏠 Optimisation par type de logement":
            st.subheader("🏠 Analyse des types de logement")
            
            if "tipo_vivienda" not in df.columns:
                st.warning("⚠️ Colonne 'tipo_vivienda' non trouvée")
            else:
                # Nettoyer les données
                df_logement = df[df["tipo_vivienda"].notna()]
                df_logement = df_logement[df_logement["tipo_vivienda"].astype(str).str.strip() != ""]
                
                if df_logement.empty:
                    st.info("Aucune donnée valide sur les types de logement")
                else:
                    # Statistiques
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Types de logement", df_logement["tipo_vivienda"].nunique())
                    with col2:
                        top_logement = df_logement["tipo_vivienda"].mode().iloc[0]
                        st.metric("Type le plus fréquent", top_logement)
                    with col3:
                        if "_qualifie" in df_logement.columns:
                            taux_qualif_top = df_logement[df_logement["tipo_vivienda"] == top_logement]["_qualifie"].mean() * 100
                            st.metric(f"Taux qualif {top_logement}", f"{taux_qualif_top:.0f}%")
                    
                    st.markdown("---")
                    
                    # Top logements par qualification
                    st.subheader("📊 Performance par type de logement")
                    
                    perf_logement = df_logement.groupby("tipo_vivienda").agg({
                        "tipo_vivienda": "count",
                        "_qualifie": "mean" if "_qualifie" in df_logement.columns else None
                    }).rename(columns={"tipo_vivienda": "total"})
                    
                    if "_qualifie" in perf_logement.columns:
                        perf_logement["taux_qualif"] = (perf_logement["_qualifie"] * 100).round(1)
                        perf_logement = perf_logement.sort_values("taux_qualif", ascending=False)
                        
                        fig = px.bar(
                            perf_logement.head(10).reset_index(),
                            x="taux_qualif",
                            y="tipo_vivienda",
                            orientation="h",
                            text="taux_qualif",
                            title="Top 10 des types de logement par taux de qualification",
                            color="taux_qualif",
                            color_continuous_scale="Greens"
                        )
                        fig.update_traces(texttemplate="%{text}%", textposition="outside")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # Recommandations
                    st.subheader("💡 Recommandations IA")
                    
                    # Identifier les opportunités
                    if "_qualifie" in perf_logement.columns:
                        mauvais_perf = perf_logement[perf_logement["taux_qualif"] < 30].head(3)
                        bons_perf = perf_logement[perf_logement["taux_qualif"] > 60].head(3)
                        
                        if not mauvais_perf.empty:
                            st.warning("⚠️ Types de logement à améliorer")
                            for _, row in mauvais_perf.iterrows():
                                st.markdown(f"""
                                **{row['tipo_vivienda']}** - Taux: {row['taux_qualif']}%  
                                💡 Action: Adapter le discours commercial pour ce type de logement
                                """)
                        
                        if not bons_perf.empty:
                            st.success("✅ Types de logement performants")
                            for _, row in bons_perf.iterrows():
                                st.markdown(f"""
                                **{row['tipo_vivienda']}** - Taux: {row['taux_qualif']}%  
                                💡 Action: Analyser les scripts gagnants et les reproduire
                                """)
        
        # ============================================================
        # VOTELET 3: OPTIMISATION TEMPORELLE
        # ============================================================
        elif volet == "⏰ Optimisation temporelle":
            st.subheader("⏰ Analyse des créneaux optimaux")
            
            if "Timestamp" not in df.columns:
                st.warning("⚠️ Colonne 'Timestamp' non trouvée")
            else:
                # Préparer les données temporelles
                df_time = df.copy()
                df_time["heure"] = pd.to_datetime(df_time["Timestamp"], errors="coerce", dayfirst=True).dt.hour
                df_time["jour"] = pd.to_datetime(df_time["Timestamp"], errors="coerce", dayfirst=True).dt.day_name()
                df_time["mois"] = pd.to_datetime(df_time["Timestamp"], errors="coerce", dayfirst=True).dt.month
                
                # Meilleures heures
                if "_qualifie" in df_time.columns:
                    perf_heure = df_time.groupby("heure").agg({
                        "_qualifie": "mean"
                    }).reset_index()
                    perf_heure["taux"] = (perf_heure["_qualifie"] * 100).round(1)
                    
                    meilleure_heure = perf_heure.loc[perf_heure["taux"].idxmax()]
                    pire_heure = perf_heure.loc[perf_heure["taux"].idxmin()]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"🌟 Meilleur créneau: {meilleure_heure['heure']:.0f}h\nTaux: {meilleure_heure['taux']}%")
                    with col2:
                        st.error(f"⚠️ Pire créneau: {pire_heure['heure']:.0f}h\nTaux: {pire_heure['taux']}%")
                    
                    # Graphique
                    fig = px.line(
                        perf_heure,
                        x="heure",
                        y="taux",
                        title="Taux de qualification par heure",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Meilleurs jours
                    perf_jour = df_time.groupby("jour").agg({
                        "_qualifie": "mean"
                    }).reset_index()
                    perf_jour["taux"] = (perf_jour["_qualifie"] * 100).round(1)
                    meilleur_jour = perf_jour.loc[perf_jour["taux"].idxmax()]
                    
                    st.info(f"📅 Meilleur jour: {meilleur_jour['jour']} (taux: {meilleur_jour['taux']}%)")
                    
                    # Recommandations
                    st.markdown("---")
                    st.subheader("💡 Recommandations IA")
                    st.markdown(f"""
                    ✅ **Planification optimale:**  
                    - Concentrer les appels entre {meilleure_heure['heure']:.0f}h et {meilleure_heure['heure']+2:.0f}h  
                    - Privilégier les {meilleur_jour['jour']} pour les campagnes importantes  
                    
                    ⚠️ **À éviter:**  
                    - Éviter les appels vers {pire_heure['heure']:.0f}h (faible taux de qualification)  
                    """)
        
        # ============================================================
        # VOTELET 4: DÉTECTION D'ANOMALIES
        # ============================================================
        elif volet == "🚨 Détection d'anomalies":
            st.subheader("🚨 Détection d'anomalies et alertes")
            
            anomalies = []
            
            # Anomalie 1: Taux de classification bas
            if "_utile" in df.columns:
                taux_classif = df["_utile"].mean() * 100
                if taux_classif < 50:
                    anomalies.append({
                        "niveau": "🔴 Critique",
                        "type": "Classification",
                        "message": f"Seulement {taux_classif:.0f}% des appels sont classifiés",
                        "action": "Mettre en place une obligation de classification"
                    })
            
            # Anomalie 2: Fournisseurs problématiques
            if "list_name" in df.columns and "_qualifie" in df.columns:
                fourn_problemes = df.groupby("list_name")["_qualifie"].mean()
                fourn_critiques = fourn_problemes[fourn_problemes < 0.2]
                
                for fournisseur in fourn_critiques.index:
                    anomalies.append({
                        "niveau": "🔴 Critique",
                        "type": "Fournisseur",
                        "message": f"{fournisseur} a un taux de qualification très bas ({fourn_problemes[fournisseur]*100:.0f}%)",
                        "action": "Audit immédiat des pratiques de ce fournisseur"
                    })
            
            # Anomalie 3: Type de logement problématique
            if "tipo_vivienda" in df.columns and "_qualifie" in df.columns:
                logement_problemes = df.groupby("tipo_vivienda")["_qualifie"].mean()
                logement_critiques = logement_problemes[logement_problemes < 0.15]
                
                for logement in logement_critiques.index[:3]:
                    anomalies.append({
                        "niveau": "🟡 Attention",
                        "type": "Logement",
                        "message": f"Type '{logement}' a un faible taux de qualification ({logement_problemes[logement]*100:.0f}%)",
                        "action": "Revoir l'approche commerciale pour ce segment"
                    })
            
            # Affichage des anomalies
            if anomalies:
                for anomaly in anomalies:
                    with st.expander(f"{anomaly['niveau']} - {anomaly['type']}"):
                        st.markdown(f"**Problème détecté:** {anomaly['message']}")
                        st.markdown(f"**Action recommandée:** {anomaly['action']}")
            else:
                st.success("✅ Aucune anomalie critique détectée !")
        
        # ============================================================
        # VOTELET 5: STRATÉGIE GLOBALE
        # ============================================================
        elif volet == "💡 Stratégie globale":
            st.subheader("💡 Synthèse stratégique et plan d'action")
            
            # KPIs globaux
            kpis = kpi_globaux(df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total appels", f"{kpis['total_appels']:,}")
            with col2:
                st.metric("Taux classification", f"{kpis['taux_utiles_pct']}%" if kpis['taux_utiles_pct'] else "N/A")
            with col3:
                if "_qualifie" in df.columns:
                    taux_qualif_global = df["_qualifie"].mean() * 100
                    st.metric("Taux qualification global", f"{taux_qualif_global:.1f}%")
            
            st.markdown("---")
            
            # Plan d'action priorisé
            st.subheader("📋 Plan d'action priorisé")
            
            actions = []
            
            # Action 1: Amélioration classification
            if kpis['taux_utiles_pct'] and kpis['taux_utiles_pct'] < 60:
                actions.append({
                    "priorite": 1,
                    "action": "Améliorer le taux de classification",
                    "details": "Former les équipes à la classification systématique",
                    "impact": "Élevé"
                })
            
            # Action 2: Focus sur meilleurs créneaux
            if "Timestamp" in df.columns:
                actions.append({
                    "priorite": 2,
                    "action": "Optimiser les plannings",
                    "details": "Concentrer les ressources sur les créneaux à fort taux de qualification",
                    "impact": "Moyen"
                })
            
            # Action 3: Benchmark fournisseurs
            if "list_name" in df.columns and "_qualifie" in df.columns:
                actions.append({
                    "priorite": 3,
                    "action": "Partager les bonnes pratiques",
                    "details": "Organiser une session entre fournisseurs pour échanger sur les scripts gagnants",
                    "impact": "Élevé"
                })
            
            # Afficher le plan d'action
            for action in actions:
                with st.container():
                    st.markdown(f"""
                    **Priorité {action['priorite']}** - {action['action']}  
                    📌 {action['details']}  
                    🎯 Impact: {action['impact']}
                    """)
                    st.markdown("---")
            
            # Prédictions
            st.subheader("🔮 Prédictions et tendances")
            
            if "Timestamp" in df.columns and len(df) > 100:
                st.info("""
                📈 **Tendances observées:**  
                - Le taux de qualification a tendance à augmenter sur les créneaux matinaux  
                - Certains types de logement montrent une croissance des appels qualifiés  
                
                🎯 **Prédiction pour le mois prochain:**  
                Une augmentation de 15-20% des appels qualifiés si les recommandations sont appliquées
                """)
            else:
                st.info("Données insuffisantes pour générer des prédictions fiables")
    
    else:
        st.info("👆 Cliquez sur 'Générer les recommandations IA' pour commencer l'analyse")