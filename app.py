# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Surveillance S. aureus 2024", layout="wide")

# Load data
@st.cache_data
def load_data():
    pheno = pd.read_excel("staph_aureus_pheno_final.xlsx")
    tests = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv", sep=',', encoding='ISO-8859-1')
    antibio = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    bacteria = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    export = pd.read_csv("Export_StaphAureus_COMPLET.csv", encoding='utf-8')

    # Nettoyage commun
    for df in [tests, antibio]:
        df.columns = df.columns.str.strip()
        if "Semaine" in df.columns:
            df.rename(columns={"Semaine": "Week"}, inplace=True)
        df["Week"] = pd.to_numeric(df["Week"], errors="coerce")

    export.columns = export.columns.str.strip()
    export.columns = export.columns.str.lower().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    return pheno, tests, antibio, bacteria, export

pheno_df, tests_df, antibio_df, bacteria_df, export_df = load_data()

st.title("\U0001F9A0 Dashboard - Surveillance Bactériologique 2024")

onglet = st.tabs(["Toutes les bactéries", "Résistance - Tests", "Résistance - Other AB", "Phénotypes", "Tableau Interactif", "Alertes par Service"])

# Onglet 1 : Liste des bactéries
with onglet[0]:
    st.header("\U0001F52C Bactéries à surveiller")
    selected_bacteria = st.selectbox("Choisissez une bactérie :", bacteria_df.iloc[:, 0].unique())
    st.dataframe(bacteria_df)
    if "staph" in selected_bacteria.lower():
        st.success("Vous avez sélectionné Staphylococcus aureus. Consultez les autres onglets pour l'analyse.")

# Fonction pour tracer % et seuil IC

def plot_resistance_graph(df, column_name, label):
    df = df.copy()
    df = df.dropna(subset=["Week", column_name])
    df = df.sort_values("Week")

    total = df[column_name].sum()
    df["p"] = df[column_name] / total
    df["p_hat"] = df["p"].rolling(window=8, min_periods=1).mean()
    df["SE"] = np.sqrt(df["p_hat"] * (1 - df["p_hat"]) / 8)
    df["upper"] = df["p_hat"] + 1.96 * df["SE"]
    df["outlier"] = df["p"] > df["upper"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Week"], y=df["p"], mode='lines+markers', name='% Hebdo', line=dict(color='black', width=3)))
    fig.add_trace(go.Scatter(x=df["Week"], y=df["upper"], mode='lines', name='Seuil IC', line=dict(color='red', dash='dot', width=3)))
    fig.add_trace(go.Scatter(x=df[df["outlier"]]["Week"], y=df[df["outlier"]]["p"], mode='markers', name='Alerte',
                             marker=dict(color='darkred', size=12, symbol='diamond')))

    fig.update_layout(title=f"% hebdomadaire - {label}", xaxis_title='Semaine', yaxis_title='%', font=dict(color='black', size=14), title_font=dict(size=20, color='black'))
    st.plotly_chart(fig, use_container_width=True)

    if df["outlier"].any():
        st.subheader("\U0001F6A8 Semaines avec alerte")
        st.dataframe(df[df["outlier"]][["Week", "p", "upper"]])
    else:
        st.info("Aucune alerte détectée selon la règle IC + moyenne mobile 8 semaines.")


# Onglet 2 : Antibiotiques - Tests
with onglet[1]:
    st.header("\U0001F489 Résistance hebdomadaire (Tests)")
    ab_cols = [col for col in tests_df.columns if "%" in col and "R" in col]
    selected_ab = st.selectbox("Choisir un antibiotique (% colonne)", ab_cols, key="tests")
    tests_df = tests_df.dropna(subset=["Week", selected_ab])
    tests_df[selected_ab] = pd.to_numeric(tests_df[selected_ab], errors="coerce") / 100
    plot_resistance_graph(tests_df, selected_ab, selected_ab)

# Onglet 3 : Antibiotiques - Other
with onglet[2]:
    st.header("\U0001F489 Résistance hebdomadaire (Other Antibiotiques)")
    ab_cols = [col for col in antibio_df.columns if "%" in col and "R" in col]
    selected_ab = st.selectbox("Choisir un antibiotique (% colonne)", ab_cols, key="other")
    antibio_df = antibio_df.dropna(subset=["Week", selected_ab])
    antibio_df[selected_ab] = pd.to_numeric(antibio_df[selected_ab], errors="coerce") / 100
    plot_resistance_graph(antibio_df, selected_ab, selected_ab)

# Onglet 4 : Phénotypes
with onglet[3]:
    st.header("Phénotypes - Analyse Graphique")
    pheno_cols = [col for col in pheno_df.columns if col != "Week"]
    for pheno in pheno_cols:
        st.subheader(pheno)
        df_plot = pheno_df[["Week", pheno]].copy()
        df_plot = df_plot.dropna()
        df_plot[pheno] = pd.to_numeric(df_plot[pheno], errors="coerce")
        total = df_plot[pheno].sum()
        if total > 0:
            df_plot["p"] = df_plot[pheno] / total
            df_plot["p_hat"] = df_plot["p"].rolling(window=8, min_periods=1).mean()
            df_plot["SE"] = np.sqrt(df_plot["p_hat"] * (1 - df_plot["p_hat"]) / 8)
            df_plot["upper"] = df_plot["p_hat"] + 1.96 * df_plot["SE"]
            df_plot["outlier"] = df_plot["p"] > df_plot["upper"]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_plot["Week"], y=df_plot["p"], mode='lines+markers', line=dict(color='black', width=3), name='% Hebdo'))
            fig.add_trace(go.Scatter(x=df_plot["Week"], y=df_plot["upper"], mode='lines', line=dict(color='red', dash='dot', width=3), name='Seuil'))
            fig.add_trace(go.Scatter(x=df_plot[df_plot["outlier"]]["Week"], y=df_plot[df_plot["outlier"]]["p"], mode='markers',
                                     marker=dict(size=12, color='darkred', symbol='diamond'), name='Alerte'))
            fig.update_layout(title=f"% hebdomadaire - {pheno}", xaxis_title='Semaine', yaxis_title='%', font=dict(color='black', size=14))
            st.plotly_chart(fig, use_container_width=True)

# Onglet 5 : Tableau Interactif
with onglet[4]:
    st.header("Exploration Interactive")
    if "week" in export_df.columns:
        export_df = export_df.sort_values("week")
        st.dataframe(export_df)
    else:
        st.error("Colonne 'week' absente de export_df")

# Onglet 6 : Alertes par Service
with onglet[5]:
    st.header("\U0001F6A8 Services concernés par des alertes")
    semaine_selectionnee = st.number_input("Semaine avec alerte", min_value=1, max_value=52, step=1)
    st.write("Colonnes dans export_df:", export_df.columns.tolist())

    required_cols = ["numero semaine", "uf", "lib_germe", "type_alerte"]
    if all(col in export_df.columns for col in required_cols):
        subset = export_df[export_df["numero semaine"] == semaine_selectionnee][["uf", "lib_germe", "type_alerte"]].drop_duplicates()
        if not subset.empty:
            st.write(f"Alertes pour la semaine {semaine_selectionnee} :")
            st.dataframe(subset)
        else:
            st.info(f"Aucune alerte trouvée pour la semaine {semaine_selectionnee}.")
    else:
        st.error("Les colonnes nécessaires sont absentes de export_df. Veuillez vérifier les noms exacts des colonnes.")
