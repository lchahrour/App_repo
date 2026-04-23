# 📞 Call Center Dashboard

Une application web interactive pour l'analyse des données d'un centre d'appels, construite avec Streamlit. Cette application permet de connecter des feuilles Google Sheets et de générer des tableaux de bord avec des KPIs et visualisations pour analyser les performances du centre d'appels.

## ✨ Fonctionnalités

- **Connexion Google Sheets** : Importation directe des données depuis Google Sheets
- **Tableaux de bord interactifs** : Visualisations avec Plotly pour une analyse approfondie
- **KPIs globaux** : Métriques clés de performance du centre d'appels
- **Analyses temporelles** : Appels par jour, mois et heure
- **Répartition par classification** : Analyse des types d'appels
- **Analyse par fournisseur** : Comparaison des performances selon les fournisseurs
- **Analyse géographique** : Appels utiles par ville et taux de remplissage des codes postaux
- **Fiabilité des données** : Détection des codes postaux non correspondants

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- Un compte Google avec accès aux Google Sheets

### Étapes d'installation

1. **Cloner le repository** :
   ```bash
   git clone <url-du-repo>
   cd call-center-dashboard
   ```

2. **Créer un environnement virtuel** :
   ```bash
   python -m venv .venv
   # Sur Windows
   .venv\Scripts\activate
   # Sur macOS/Linux
   source .venv/bin/activate
   ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

## 📋 Utilisation

1. **Démarrer l'application** :
   ```bash
   streamlit run app.py
   ```

2. **Accéder à l'interface** :
   Ouvrez votre navigateur à l'adresse indiquée (généralement `http://localhost:8501`)

3. **Connexion aux données** :
   - Dans la barre latérale, collez l'URL de votre Google Sheet
   - Cliquez sur "📂 Charger les feuilles"
   - Sélectionnez les feuilles à analyser
   - Chargez les données

4. **Explorer les analyses** :
   - Consultez les KPIs globaux
   - Naviguez entre les différentes visualisations
   - Utilisez les filtres pour affiner l'analyse

## 📊 Structure du projet

```
├── app.py                 # Application principale Streamlit
├── analyse.py             # Fonctions d'analyse des données
├── google_selector.py     # Module de connexion Google Sheets
├── requirements.txt       # Dépendances Python
├── app.spec              # Configuration PyInstaller
├── test.py               # Tests unitaires
└── README.md             # Documentation du projet
```

## 🛠️ Technologies utilisées

- **Streamlit** : Framework web pour les applications de données
- **Pandas** : Manipulation et analyse des données
- **Plotly** : Visualisations interactives
- **GSpread** : Interface Python pour Google Sheets
- **Google Auth** : Authentification Google

## 📈 KPIs et analyses disponibles

- Nombre total d'appels
- Taux d'appels utiles
- Répartition temporelle (jour, mois, heure)
- Classification des appels
- Performance par fournisseur
- Analyse géographique par ville
- Fiabilité des codes postaux
- Comparaisons de codes postaux

## 🔧 Configuration

### Google Sheets

Pour utiliser l'application avec vos propres données Google Sheets :

1. Rendez votre feuille accessible publiquement :
   - Ouvrez votre Google Sheet
   - Cliquez sur **Partager** (🔗 en haut à droite)
   - Sélectionnez **"Toute personne disposant du lien"**
   - Copiez l'URL complète

2. Assurez-vous que vos données respectent le format attendu :
   - Colonne "Timestamp" pour les dates/heures
   - Colonne "Classification" pour le type d'appel
   - Colonnes géographiques (ville, code postal, etc.)

## 🧪 Tests

Pour exécuter les tests :
```bash
python test.py
```

## 📝 Notes de développement

- L'application utilise un cache de session Streamlit pour optimiser les performances
- Les données sont chargées une seule fois par session
- Les visualisations sont générées dynamiquement avec Plotly

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer de nouvelles fonctionnalités
- Améliorer la documentation
- Soumettre des pull requests

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.