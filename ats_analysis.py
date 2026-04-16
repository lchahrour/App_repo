# ats_analysis.py
import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
import io


# ─────────────────────────────────────────────
# PARSER CSV ATS
# ─────────────────────────────────────────────

def parse_ats_csv(content: str, filename: str) -> dict:
    """
    Parse un fichier CSV ATS au format :
        "CAMPAIGN: CMP_01"
        "List ID #104: EXT FICH SERV 51 MIXT"
        "DISPOSITION","CALLS","DURATION","HANDLE TIME"
        "NA - No Answer AutoDial","7594","0:00:00","0:00:00"
        "TOTALS:","11770","2:21:53","0:00:00"
    Retourne un dict avec les campagnes et leurs listes.
    """
    result = {
        "filename": filename,
        "campaigns": []
    }

    current_campaign = None
    current_list = None
    in_data_section = False
    headers = []

    lines = content.splitlines()

    for raw_line in lines:
        line = raw_line.strip().strip('"')

        if not line:
            continue

        # Détection campagne
        if line.startswith("CAMPAIGN:"):
            campaign_name = line.replace("CAMPAIGN:", "").strip()
            current_campaign = {
                "name": campaign_name,
                "lists": []
            }
            result["campaigns"].append(current_campaign)
            current_list = None
            in_data_section = False
            continue

        # Détection List ID
        if line.startswith("List ID #"):
            list_name = line.strip()
            current_list = {
                "name": list_name,
                "dispositions": [],
                "totals": None,
                "no_calls": False
            }
            if current_campaign is not None:
                current_campaign["lists"].append(current_list)
            else:
                # Pas de campagne définie, on en crée une par défaut
                current_campaign = {"name": "CAMPAIGN_DEFAULT", "lists": [current_list]}
                result["campaigns"].append(current_campaign)
            in_data_section = False
            headers = []
            continue

        # Détection NO CALLS
        if "NO CALLS FOUND" in line:
            if current_list is not None:
                current_list["no_calls"] = True
            in_data_section = False
            continue

        # Détection en-tête colonnes
        if "DISPOSITION" in line and "CALLS" in line:
            headers = [h.strip().strip('"') for h in raw_line.split(",")]
            in_data_section = True
            continue

        # Lignes de données
        if in_data_section and current_list is not None:
            parts = [p.strip().strip('"') for p in raw_line.split(",")]
            if not parts or not parts[0]:
                continue

            # Ligne TOTALS
            if parts[0].upper().startswith("TOTALS"):
                try:
                    current_list["totals"] = {
                        "calls":       int(parts[1]) if len(parts) > 1 else 0,
                        "duration":    parts[2] if len(parts) > 2 else "0:00:00",
                        "handle_time": parts[3] if len(parts) > 3 else "0:00:00"
                    }
                except (ValueError, IndexError):
                    pass
                continue

            # Ligne disposition normale
            try:
                disp = {
                    "disposition": parts[0],
                    "calls":       int(parts[1]) if len(parts) > 1 else 0,
                    "duration":    parts[2] if len(parts) > 2 else "0:00:00",
                    "handle_time": parts[3] if len(parts) > 3 else "0:00:00"
                }
                current_list["dispositions"].append(disp)
            except (ValueError, IndexError):
                continue

    return result


def ats_to_dataframe(parsed: dict) -> pd.DataFrame:
    """Convertit les données parsées en DataFrame plat pour affichage."""
    rows = []
    for campaign in parsed.get("campaigns", []):
        for lst in campaign.get("lists", []):
            if lst.get("no_calls"):
                continue
            for disp in lst.get("dispositions", []):
                rows.append({
                    "Fichier":      parsed["filename"],
                    "Campagne":     campaign["name"],
                    "Liste":        lst["name"],
                    "Disposition":  disp["disposition"],
                    "Appels":       disp["calls"],
                    "Durée":        disp["duration"],
                    "Handle Time":  disp["handle_time"]
                })
    return pd.DataFrame(rows)


def resumer_ats_pour_gemini(all_parsed: list[dict]) -> dict:
    """
    Construit un résumé compact de tous les fichiers ATS
    pour l'envoyer à Gemini sans dépasser le context window.
    """
    summary = {"fichiers": []}

    for parsed in all_parsed:
        fichier_summary = {
            "nom": parsed["filename"],
            "campaigns": []
        }
        for campaign in parsed.get("campaigns", []):
            camp_summary = {
                "nom": campaign["name"],
                "listes": []
            }
            for lst in campaign.get("lists", []):
                if lst.get("no_calls"):
                    camp_summary["listes"].append({
                        "nom": lst["name"],
                        "statut": "Aucun appel trouvé"
                    })
                    continue

                totals = lst.get("totals", {})
                top_disps = sorted(
                    lst.get("dispositions", []),
                    key=lambda x: x["calls"],
                    reverse=True
                )[:5]

                camp_summary["listes"].append({
                    "nom":          lst["name"],
                    "total_appels": totals.get("calls", 0) if totals else 0,
                    "duree_totale": totals.get("duration", "N/A") if totals else "N/A",
                    "top_dispositions": [
                        {"code": d["disposition"], "appels": d["calls"]}
                        for d in top_disps
                    ]
                })
            fichier_summary["campaigns"].append(camp_summary)
        summary["fichiers"].append(fichier_summary)

    return summary


# ─────────────────────────────────────────────
# GEMINI POUR ATS
# ─────────────────────────────────────────────

def analyser_ats_avec_gemini(api_key: str, summary: dict) -> dict | None:
    """Envoie le résumé ATS à Gemini et retourne les recommandations."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        st.error(f"❌ Erreur connexion Gemini: {e}")
        return None

    prompt = f"""
Tu es un expert en centres d'appels outbound. Analyse ces données ATS (Automated Telephone System).

Données ATS:
{json.dumps(summary, ensure_ascii=False, indent=2)}

Légende des codes disposition courants:
- NA / No Answer : pas de réponse
- AB / Busy : occupé
- AA / Answering Machine : répondeur automatique
- ADC / Disconnected : numéro non attribué
- DROP : agent non disponible (problème capacité)
- SHCALL / Short Call : appel très court (raccroché)
- XFER / Transferred : appel transféré (potentiellement utile)
- PDROP : drop pré-routage

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après, sans balises markdown :
{{
    "resume_global": "synthèse en 2-3 phrases de la qualité globale des listes",
    "taux_contact_moyen": "estimation du taux de contact réel en %",
    "points_forts": ["point fort 1", "point fort 2"],
    "points_faibles": ["point faible 1", "point faible 2"],
    "analyse_par_fichier": [
        {{
            "fichier": "nom du fichier",
            "qualite": "bonne / moyenne / faible",
            "observation": "observation principale en 1 phrase",
            "liste_recommandee": "nom de la meilleure liste"
        }}
    ],
    "actions_prioritaires": [
        {{"action": "...", "pourquoi": "...", "impact": "..."}},
        {{"action": "...", "pourquoi": "...", "impact": "..."}},
        {{"action": "...", "pourquoi": "...", "impact": "..."}}
    ],
    "recommandation_horaire": "conseil sur les horaires d'appel basé sur les dispositions",
    "prediction": "prédiction sur le rendement si les actions sont appliquées"
}}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text).strip()

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        st.error("Aucun JSON trouvé dans la réponse Gemini")
        st.code(text[:500])
        return None

    except json.JSONDecodeError as e:
        st.error(f"Erreur parsing JSON: {e}")
        st.code(text[:500])
        return None
    except Exception as e:
        st.error(f"Erreur API Gemini: {e}")
        return None


# ─────────────────────────────────────────────
# ONGLET STREAMLIT
# ─────────────────────────────────────────────

def render_ats_tab(api_key_input: str = None):
    """
    Rendu complet de l'onglet 'Analyse des ATS par IA'.
    Appelez cette fonction dans votre tab :
        with tab_ats:
            render_ats_tab(api_key_input=api_key_input)
    Si api_key_input est None, le champ de saisie est affiché dans cet onglet.
    """
    import plotly.express as px

    st.header("📋 Analyse des ATS par IA")
    st.markdown("---")

    # ── Clé API ──────────────────────────────
    if not api_key_input:
        api_key_input = st.text_input(
            "🔑 Clé API Gemini",
            type="password",
            placeholder="AIza...",
            key="ats_api_key"
        )
        if not api_key_input:
            st.info("👆 Entrez votre clé API Gemini pour activer l'analyse IA")
            st.stop()

    # ── Upload fichiers ───────────────────────
    st.subheader("📤 Importer les fichiers ATS")
    uploaded_files = st.file_uploader(
        "Glissez vos fichiers CSV ATS (un ou plusieurs)",
        type=["csv", "txt"],
        accept_multiple_files=True,
        key="ats_files"
    )

    if not uploaded_files:
        st.info("📂 Importez au moins un fichier CSV ATS pour commencer")
        st.stop()

    # ── Parsing ───────────────────────────────
    all_parsed = []
    all_dfs    = []

    for f in uploaded_files:
        try:
            content = f.read().decode("utf-8", errors="replace")
            parsed  = parse_ats_csv(content, f.name)
            df_f    = ats_to_dataframe(parsed)
            all_parsed.append(parsed)
            if not df_f.empty:
                all_dfs.append(df_f)
        except Exception as e:
            st.warning(f"⚠️ Erreur lecture {f.name} : {e}")

    if not all_parsed:
        st.error("❌ Aucun fichier valide parsé")
        st.stop()

    df_all = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

    # ── Aperçu données ────────────────────────
    with st.expander("📊 Aperçu des données parsées", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fichiers chargés", len(all_parsed))
        col2.metric("Total appels", f"{df_all['Appels'].sum():,}" if not df_all.empty else "0")
        col3.metric("Campagnes",
                    sum(len(p["campaigns"]) for p in all_parsed))
        col4.metric("Listes actives",
                    len(df_all["Liste"].unique()) if not df_all.empty else 0)

        if not df_all.empty:
            st.dataframe(
                df_all.sort_values("Appels", ascending=False),
                use_container_width=True,
                height=300
            )

    # ── Graphiques rapides ────────────────────
    if not df_all.empty:
        st.markdown("---")
        st.subheader("📈 Visualisation rapide")

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            df_disp = (df_all.groupby("Disposition")["Appels"]
                       .sum().reset_index()
                       .sort_values("Appels", ascending=False)
                       .head(10))
            fig1 = px.bar(
                df_disp, x="Appels", y="Disposition",
                orientation="h", title="Top 10 Dispositions",
                color="Appels", color_continuous_scale="Blues"
            )
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)

        with col_g2:
            df_liste = (df_all.groupby("Liste")["Appels"]
                        .sum().reset_index()
                        .sort_values("Appels", ascending=False)
                        .head(10))
            fig2 = px.bar(
                df_liste, x="Appels", y="Liste",
                orientation="h", title="Appels par liste",
                color="Appels", color_continuous_scale="Greens"
            )
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Bouton analyse IA ─────────────────────
    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        analyse_btn = st.button(
            "🤖 ANALYSER AVEC GEMINI",
            type="primary",
            use_container_width=True,
            key="ats_analyse_btn"
        )

    if analyse_btn:
        summary = resumer_ats_pour_gemini(all_parsed)
        with st.spinner("🤖 Gemini analyse vos fichiers ATS..."):
            resultat = analyser_ats_avec_gemini(api_key_input, summary)

        if resultat:
            st.balloons()
            st.session_state["ats_analyse_resultat"] = resultat
        else:
            st.error("❌ Échec de l'analyse IA")

    # ── Affichage résultats ───────────────────
    if "ats_analyse_resultat" in st.session_state:
        r = st.session_state["ats_analyse_resultat"]
        st.markdown("---")
        st.success("✅ Analyse terminée")

        # Résumé global
        st.subheader("📌 Résumé global")
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            st.info(r.get("resume_global", "N/A"))
        with col_r2:
            st.metric("Taux contact estimé", r.get("taux_contact_moyen", "N/A"))

        # Points forts / faibles
        col_pf1, col_pf2 = st.columns(2)
        with col_pf1:
            st.subheader("✅ Points forts")
            for pt in r.get("points_forts", []):
                st.success(f"• {pt}")
        with col_pf2:
            st.subheader("⚠️ Points faibles")
            for pt in r.get("points_faibles", []):
                st.warning(f"• {pt}")

        # Analyse par fichier
        if r.get("analyse_par_fichier"):
            st.markdown("---")
            st.subheader("📁 Analyse par fichier")
            qualite_color = {"bonne": "✅", "moyenne": "🟡", "faible": "🔴"}
            for item in r["analyse_par_fichier"]:
                q = item.get("qualite", "moyenne").lower()
                icon = qualite_color.get(q, "🔵")
                with st.expander(f"{icon} {item.get('fichier', 'N/A')} — qualité {q}"):
                    st.write(f"**Observation :** {item.get('observation', 'N/A')}")
                    st.write(f"**Liste recommandée :** {item.get('liste_recommandee', 'N/A')}")

        # Actions prioritaires
        if r.get("actions_prioritaires"):
            st.markdown("---")
            st.subheader("🚀 Actions prioritaires")
            for action in r["actions_prioritaires"]:
                st.markdown(f"""
**👉 {action.get('action', '')}**  
📌 Pourquoi : {action.get('pourquoi', '')}  
🎯 Impact : {action.get('impact', '')}
""")

        # Recommandation horaire + prédiction
        st.markdown("---")
        col_h, col_p = st.columns(2)
        with col_h:
            st.subheader("⏰ Recommandation horaire")
            st.info(r.get("recommandation_horaire", "N/A"))
        with col_p:
            st.subheader("🔮 Prédiction")
            st.info(r.get("prediction", "N/A"))

        # Export
        st.markdown("---")
        st.download_button(
            "📥 Exporter l'analyse JSON",
            data=json.dumps(r, ensure_ascii=False, indent=2),
            file_name="analyse_ats_ia.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("---")