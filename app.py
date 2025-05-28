# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Load data
@st.cache_data

def load_data():
    pheno = pd.read_excel("staph_aureus_pheno_final.xlsx")
    tests = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv", sep=';', encoding='ISO-8859-1')
    antibio = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    bacteria = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    export = pd.read_csv("Export_StaphAureus_COMPLET.csv", encoding='utf-8')
    return pheno, tests, antibio, bacteria, export

pheno_df, tests_df, antibio_df, bacteria_df, export_df = load_data()

st.set_page_config(page_title="Surveillance S. aureus 2024", layout="wide")
st.title("\U0001F9A0 Dashboard - Surveillance Bactériologique 2024")

# Tabs
onglet = st.tabs(["Toutes les bactéries", "Antibiotiques", "Phénotypes", "Tableau Interactif", "Alertes par Service"])

# Onglet 1 : Liste des bactéries et lien vers S. aureus
with onglet[0]:
    st.header("\U0001F52C Bactéries à surveiller")
    selected_bacteria = st.selectbox("Choisissez une bactérie :", bacteria_df.iloc[:, 0].unique())
    st.dataframe(bacteria_df)

    if "staph" in selected_bacteria.lower():
        st.success("Vous avez sélectionné Staphylococcus aureus. Consultez les autres onglets pour l'analyse.")

# Onglet 2 : Résistance Antibiotiques
with onglet[1]:
    st.header("\U0001F489 Résistance hebdomadaire aux antibiotiques")
    selected_ab = st.selectbox("Choisir un antibiotique", antibio_df.columns[1:])

    df = antibio_df[["Week", selected_ab]].copy()
    df.columns = ["Week", "R"]
    df["Total"] = tests_df.iloc[:, 0]
    df["p"] = df["R"] / df["Total"]
    df["n_last_8"] = df["Total"].rolling(window=8, min_periods=1).sum()
    df["event_last_8"] = df["R"].rolling(window=8, min_periods=1).sum()
    df["p_hat"] = df["event_last_8"] / df["n_last_8"]
    df["SE"] = np.sqrt(df["p_hat"] * (1 - df["p_hat"]) / df["Total"])
    df["upper"] = df["p_hat"] + 1.96 * df["SE"]
    df["outlier"] = df["p"] > df["upper"]

    if selected_ab.lower() == "vancomycine":
        df["outlier"] = df["R"] >= 1

    fig = px.line(df, x="Week", y="p", markers=True, title=f"% de résistance hebdo - {selected_ab}")
    fig.add_scatter(x=df["Week"], y=df["upper"], mode="lines", name="Seuil d'alerte", line=dict(dash="dash", color="red"))
    fig.update_traces(marker=dict(size=10, color=df["outlier"].map({True: "darkred", False: "blue"})))
    st.plotly_chart(fig, use_container_width=True)

# Onglet 3 : Phénotypes
with onglet[2]:
    st.header("\U0001F9EC Suivi des phénotypes de S. aureus")
    selected_pheno = st.selectbox("Choisir un phénotype", pheno_df.columns[1:-1])

    df = pheno_df[["Week", selected_pheno]].copy()
    df.columns = ["Week", "R"]
    df["Total"] = pheno_df[["MRSA", "VRSA", "Wild", "Other"]].sum(axis=1)

    if selected_pheno.lower() == "vrsa":
        df["outlier"] = df["R"] >= 1
    else:
        df["p"] = df["R"] / df["Total"]
        df["n_last_8"] = df["Total"].rolling(window=8, min_periods=1).sum()
        df["event_last_8"] = df["R"].rolling(window=8, min_periods=1).sum()
        df["p_hat"] = df["event_last_8"] / df["n_last_8"]
        df["SE"] = np.sqrt(df["p_hat"] * (1 - df["p_hat"]) / df["Total"])
        df["upper"] = df["p_hat"] + 1.96 * df["SE"]
        df["outlier"] = df["p"] > df["upper"]

    fig = px.line(df, x="Week", y="R", markers=True, title=f"Cas hebdo - {selected_pheno}")
    fig.update_traces(marker=dict(size=10, color=df["outlier"].map({True: "darkred", False: "green"})))
    st.plotly_chart(fig, use_container_width=True)

# Onglet 4 : Tableau interactif
with onglet[3]:
    st.header("\U0001F4C4 Vue complète filtrable")
    st.dataframe(pheno_df)

# Onglet 5 : Services avec alertes
with onglet[4]:
    st.header("\U0001F6A8 Services concernés par des alertes")
    st.dataframe(export_df[["uf", "numéro semaine", "lib_germe"]].drop_duplicates())
