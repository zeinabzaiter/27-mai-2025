# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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

    # Nettoyage export
    export.columns = export.columns.str.strip()
    export.columns = export.columns.str.lower().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    st.write("Colonnes disponibles dans export_df :", export.columns.tolist())

    return pheno, tests, antibio, bacteria, export

pheno_df, tests_df, antibio_df, bacteria_df, export_df = load_data()

st.title("\U0001F9A0 Dashboard - Surveillance Bactériologique 2024")

# Tabs
onglet = st.tabs(["Toutes les bactéries", "Résistance - Tests", "Résistance - Other AB", "Phénotypes", "Tableau Interactif", "Alertes par Service"])

# Onglet 1 : Liste des bactéries
with onglet[0]:
    st.header("\U0001F52C Bactéries à surveiller")
    selected_bacteria = st.selectbox("Choisissez une bactérie :", bacteria_df.iloc[:, 0].unique())
    st.dataframe(bacteria_df)
    if "staph" in selected_bacteria.lower():
        st.success("Vous avez sélectionné Staphylococcus aureus. Consultez les autres onglets pour l'analyse.")

# Fonction commune

def tracer_resistance(df, source):
    ab_cols = [col for col in df.columns if "%" in col and "R" in col]
    selected_ab = st.selectbox("Choisir un antibiotique (% colonne)", ab_cols, key=source)

    df_plot = df[["Week", selected_ab]].copy()
    df_plot.columns = ["Week", "p"]
    df_plot["p"] = pd.to_numeric(df_plot["p"], errors="coerce") / 100

    df_plot = df_plot.dropna(subset=["Week", "p"])
    df_plot = df_plot.sort_values("Week")

    df_plot["n_last_8"] = 8
    df_plot["event_last_8"] = df_plot["p"].rolling(window=8, min_periods=1).sum()
    df_plot["p_hat"] = df_plot["event_last_8"] / df_plot["n_last_8"]
    df_plot["SE"] = np.sqrt(df_plot["p_hat"] * (1 - df_plot["p_hat"]) / df_plot["n_last_8"])
    df_plot["upper"] = df_plot["p_hat"] + 1.96 * df_plot["SE"]
    df_plot["outlier"] = df_plot["p"] > df_plot["upper"]

    fig = px.line(df_plot, x="Week", y="p", markers=True, title=f"% de résistance hebdo - {selected_ab}")
    fig.add_scatter(x=df_plot["Week"], y=df_plot["upper"], mode="lines", name="Seuil d'alerte", line=dict(dash="dot", color="red"))
    fig.add_scatter(x=df_plot[df_plot["outlier"]]["Week"], y=df_plot[df_plot["outlier"]]["p"], mode="markers", name="Alerte", marker=dict(size=12, color="darkred"))
    st.plotly_chart(fig, use_container_width=True)

    if df_plot["outlier"].any():
        st.subheader("\U0001F6A8 Semaines avec alerte")
        st.dataframe(df_plot[df_plot["outlier"]][["Week", "p", "upper"]])
    else:
        st.info("Aucune alerte détectée selon la règle IC + moyenne mobile 8 semaines.")

# Onglet 2 : Antibiotiques - Tests
with onglet[1]:
    st.header("\U0001F489 Résistance hebdomadaire (Tests)")
    tracer_resistance(tests_df, source="tests")

# Onglet 3 : Antibiotiques - Other
with onglet[2]:
    st.header("\U0001F489 Résistance hebdomadaire (Other Antibiotiques)")
    tracer_resistance(antibio_df, source="other")

# Onglet 4 à 6 : inchangés (Phénotypes, Interactif, Alertes)
# [Code existant conservé ici, sans modification, sauf si besoin sur demande]
