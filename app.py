# app.py - Fichier principal du tableau de bord interactif avec Streamlit

import streamlit as st

# Configuration générale de la page
st.set_page_config(
    page_title="Dashboard Résistance Antibiotiques",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre général du dashboard
st.title("🧪 Dashboard interactif de Résistance aux Antibiotiques")

# Barre latérale pour navigation
st.sidebar.header("🔎 Navigation")
st.sidebar.markdown("""
- **📊 [Toutes les bactéries](./pages/1_📊_Toutes_les_bactéries.py)**
- **🦠 [Résistance - Tests](./pages/2_🦠_Résistance_Tests.py)**
- **🧫 [Résistance - Other AB](./pages/3_🧫_Résistance_Other_AB.py)**
- **📈 [Phénotypes](./pages/4_📈_Phénotypes.py)**
- **📋 [Tableau Interactif](./pages/5_📋_Tableau_Interactif.py)**
- **🚨 [Alertes par Service](./pages/6_🚨_Alertes_Service.py)**
""")

# Description principale
def main():
    st.markdown("""
    Bienvenue dans votre tableau de bord interactif conçu spécialement pour :

    - **Suivre en temps réel** l'évolution de la résistance aux antibiotiques.
    - Identifier clairement les seuils d'alertes statistiques (IC95%, moyennes mobiles sur 8 semaines).
    - Visualiser et analyser les phénotypes bactériens.
    - Générer des alertes visuelles en fonction des données.

    **📍 Utilisez la barre latérale à gauche pour naviguer entre les différentes sections du tableau de bord.**

    ---

    ⚙️ **Instructions techniques :**

    1. Déposez toutes vos données (`.xlsx` ou `.csv`) dans le dossier `data/`.
    2. Assurez-vous que toutes les dépendances nécessaires sont installées (`requirements.txt`).
    3. Lancez le tableau de bord localement via la commande :
    ```bash
    streamlit run app.py
    ```

    **📦 Déploiement :** Connectez ce tableau de bord à GitHub pour un déploiement automatique sur Streamlit Cloud.

    ---

    🛠 **Support technique :** Pour toute question ou assistance, contactez l'équipe technique.
    """)

if __name__ == "__main__":
    main()
