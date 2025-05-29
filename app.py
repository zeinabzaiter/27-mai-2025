import streamlit as st
import pandas as pd

# Chargement des données
@st.cache_data
def load_data():
    return pd.read_csv("Export_StaphAureus_COMPLET.csv")

export_df = load_data()

# Titre principal
st.title("Dashboard - Surveillance Bactériologique 2024")

# Définition des onglets
onglet = st.tabs([
    "Toutes les bactéries",
    "Résistance - Tests",
    "Résistance - Other AB",
    "Phénotypes",
    "Tableau Interactif",
    "Alertes par Service"
])

# Onglet 1 - Toutes les bactéries
with onglet[0]:
    st.header("Toutes les bactéries")
    st.dataframe(export_df.head())

# Onglet 2 - Résistance - Tests
with onglet[1]:
    st.header("Résistance - Tests")
    st.write("Analyse des résistances aux tests antibiotiques")
    # Ajoute ici tes analyses spécifiques si besoin

# Onglet 3 - Résistance - Other AB
with onglet[2]:
    st.header("Résistance - Other AB")
    st.write("Analyse des autres antibiotiques")
    # Ajoute ici tes analyses spécifiques si besoin

# Onglet 4 - Phénotypes
with onglet[3]:
    st.header("Phénotypes - analyse interactive")
    col_semaine = next((col for col in export_df.columns if "week" in col.lower() or "semaine" in col.lower()), None)

    if col_semaine:
        df_plot = export_df.copy()
        df_plot = df_plot.sort_values(by=col_semaine)

        if "p" in df_plot.columns:
            df_plot["rolling"] = df_plot["p"].rolling(window=8, min_periods=1).mean()
            st.line_chart(df_plot[[col_semaine, "rolling"]].set_index(col_semaine))
        else:
            st.warning("La colonne 'p' est absente de export_df.")
    else:
        st.error("Colonne 'semaine' ou 'week' absente de export_df")

# Onglet 5 - Tableau Interactif
with onglet[4]:
    st.header("Exploration Interactive")
    week_col = next((col for col in export_df.columns if "week" in col or "semaine" in col), None)
    if week_col is None:
        st.error("Colonne 'week' absente de export_df")
    else:
        df_plot = export_df.sort_values(week_col)
        st.dataframe(df_plot)

# Onglet 6 - Alertes par Service
with onglet[5]:
    st.header("\U0001F6A8 Services concernés par des alertes")
    semaine_selectionnee = st.number_input("Semaine avec alerte", min_value=1, max_value=52, step=1)

    col_uf = next((col for col in export_df.columns if "uf" in col), None)
    col_germe = next((col for col in export_df.columns if "germe" in col), None)
    col_alerte = next((col for col in export_df.columns if "alerte" in col), None)
    col_semaine = next((col for col in export_df.columns if "week" in col or "semaine" in col), None)

    if None in [col_uf, col_germe, col_alerte, col_semaine]:
        st.error("Colonnes requises manquantes dans export_df. Vérifiez les noms.")
    else:
        subset = export_df[export_df[col_semaine] == semaine_selectionnee][[col_uf, col_germe, col_alerte]].drop_duplicates()
        if not subset.empty:
            st.write(f"Alertes pour la semaine {semaine_selectionnee} :")
            st.dataframe(subset)
        else:
            st.info(f"Aucune alerte trouvée pour la semaine {semaine_selectionnee}.")
