# ai_recommendations.py
import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re

class GeminiAdvisor:
    def __init__(self, api_key=None):
        """Initialise l'advisor avec Gemini API"""
        if api_key is None:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
            except:
                self.model = None
                self.is_configured = False
                return
        
        try:
            genai.configure(api_key=api_key)
            
            # Utiliser un modèle disponible - ESSAYEZ CELUI-CI D'ABORD
            # Option 1: gemini-pro (le plus stable)
            try:
                self.model = genai.GenerativeModel('gemini-3-flash-preview')
            except:
                # Option 2: gemini-1.0-pro
                try:
                    self.model = genai.GenerativeModel('gemini-3-flash-preview')
                except:
                    # Option 3: gemini-1.5-pro
                    self.model = genai.GenerativeModel('gemini-3-flash-preview')
            
            self.is_configured = True
            st.success("✅ Modèle Gemini chargé avec succès")
            
        except Exception as e:
            st.error(f"❌ Erreur de configuration: {str(e)}")
            self.model = None
            self.is_configured = False
    
    def analyser_tous_les_volets(self, df):
        """Analyse COMPLÈTE du dashboard"""
        if not self.is_configured:
            return None
        
        # Préparer les données
        contexte = self._preparer_contexte_complet(df)
        prompt = self._construire_prompt(contexte)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parser_reponse(response.text)
        except Exception as e:
            st.error(f"Erreur API: {str(e)}")
            return None
    
    def _preparer_contexte_complet(self, df):
        """Prépare les données pour l'IA"""
        
        contexte = {
            "total_appels": len(df),
            "analyse_fournisseurs": [],
            "analyse_horaire": {},
            "analyse_logements": []
        }
        
        # Analyse fournisseurs
        if "list_name" in df.columns:
            for fournisseur in df["list_name"].unique()[:10]:
                df_f = df[df["list_name"] == fournisseur]
                total = len(df_f)
                
                # Calcul taux classification
                taux = 0
                if "Classification" in df.columns:
                    non_utiles = ["", "nan", "none", "non trouvé", "non trouve"]
                    utile_mask = ~df_f["Classification"].astype(str).str.lower().str.strip().isin(non_utiles)
                    taux = round(utile_mask.sum() / total * 100, 1) if total > 0 else 0
                
                contexte["analyse_fournisseurs"].append({
                    "nom": fournisseur,
                    "appels": total,
                    "taux_classification": taux
                })
        
        # Analyse horaire
        if "Timestamp" in df.columns and "Classification" in df.columns:
            df_time = df.copy()
            df_time["datetime"] = pd.to_datetime(df_time["Timestamp"], errors="coerce", dayfirst=True)
            df_time = df_time.dropna(subset=["datetime"])
            df_time["heure"] = df_time["datetime"].dt.hour
            
            non_utiles = ["", "nan", "none", "non trouvé", "non trouve"]
            utile_mask = ~df_time["Classification"].astype(str).str.lower().str.strip().isin(non_utiles)
            
            perf_heure = {}
            meilleure_heure = 0
            meilleur_taux = 0
            heure_plus_appels = 0
            max_appels = 0
            
            for heure in range(24):
                df_h = df_time[df_time["heure"] == heure]
                if len(df_h) > 0:
                    taux = round(utile_mask[df_h.index].sum() / len(df_h) * 100, 1)
                    perf_heure[heure] = {"taux": taux, "appels": len(df_h)}
                    
                    if taux > meilleur_taux:
                        meilleur_taux = taux
                        meilleure_heure = heure
                    
                    if len(df_h) > max_appels:
                        max_appels = len(df_h)
                        heure_plus_appels = heure
            
            contexte["analyse_horaire"] = {
                "meilleure_heure": meilleure_heure,
                "meilleur_taux": meilleur_taux,
                "heure_plus_appels": heure_plus_appels,
                "volume_max": max_appels,
                "performance_par_heure": perf_heure
            }
        
        # Analyse logements
        if "tipo_vivienda" in df.columns and "Classification" in df.columns:
            df_log = df[df["tipo_vivienda"].notna()]
            df_log = df_log[df_log["tipo_vivienda"].astype(str).str.strip() != ""]
            
            non_utiles = ["", "nan", "none", "non trouvé", "non trouve"]
            utile_mask = ~df_log["Classification"].astype(str).str.lower().str.strip().isin(non_utiles)
            
            for logement in df_log["tipo_vivienda"].unique()[:10]:
                df_l = df_log[df_log["tipo_vivienda"] == logement]
                total = len(df_l)
                taux = round(utile_mask[df_l.index].sum() / total * 100, 1) if total > 0 else 0
                
                contexte["analyse_logements"].append({
                    "type": str(logement),
                    "appels": total,
                    "taux_classification": taux
                })
        
        return contexte
    
    def _construire_prompt(self, contexte):
        """Construit le prompt pour Gemini"""
        
        prompt = f"""
        Analyse ces données de centre d'appels:
        
        Total appels: {contexte.get('total_appels', 0)}
        
        Fournisseurs: {json.dumps(contexte.get('analyse_fournisseurs', []), ensure_ascii=False)}
        
        Horaires: {json.dumps(contexte.get('analyse_horaire', {}), ensure_ascii=False)}
        
        Logements: {json.dumps(contexte.get('analyse_logements', [])[:5], ensure_ascii=False)}
        
        Réponds UNIQUEMENT en JSON avec cette structure exacte:
        {{
            "resume_executif": "synthèse de la situation en 2 phrases",
            "actions_prioritaires": [
                {{"action": "action 1", "pourquoi": "justification", "impact": "impact attendu"}},
                {{"action": "action 2", "pourquoi": "justification", "impact": "impact attendu"}},
                {{"action": "action 3", "pourquoi": "justification", "impact": "impact attendu"}}
            ],
            "recommandations": {{
                "horaires": "recommandation sur les horaires",
                "fournisseurs": "recommandation sur les fournisseurs",
                "logements": "recommandation sur les logements"
            }},
            "prediction": "prédiction pour le mois prochain en 1 phrase"
        }}
        
        IMPORTANT: Réponds UNIQUEMENT en JSON, sans texte avant ou après.
        """
        
        return prompt
    
    def _parser_reponse(self, response_text):
        """Parse la réponse JSON de Gemini"""
        try:
            # Nettoyer la réponse
            response_text = response_text.strip()
            
            # Enlever les marqueurs markdown si présents
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Trouver le JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception as e:
            st.error(f"Erreur parsing: {str(e)}")
            return None