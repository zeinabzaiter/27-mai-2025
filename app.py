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
    export = pd.read_csv("Export_Antibiogramme_2024_anonymise.csv", sep=';', encoding='ISO-8859-1', low_memory=False)
    return pheno, tests, antibio, bacteria, export

pheno_df, tests_df, antibio_df, bacteria_df, export_df = load_data()

st.set_page_config(page_title="Surveillance S. aureus 2024", layout="wide")
st.title("\U0001F9A0 Dashboard - Staphylococcus aureus 2024")

# Onglets
onglet = st.tabs(["Bactéries", "Antibiotiques", "Phénotypes"])

# Onglet Bactéries
with onglet[0]:
    st.header("\U0001F52C Résumé des bactéries à surveiller")
    st.dataframe(bacteria_df)

# Onglet Antibiotiques
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

    fig = px.line(df, x="Week", y="p", markers=True, title=f"% de résistance hebdo - {selected_ab}")
    fig.add_scatter(x=df["Week"], y=df["upper"], mode="lines", name="Seuil d'alerte", line=dict(dash="dash", color="red"))
    fig.update_traces(marker=dict(size=10, color=df["outlier"].map({True: "darkred", False: "blue"})))
    st.plotly_chart(fig, use_container_width=True)

# Onglet Phénotypes
with onglet[2]:
    st.header("\U0001F9EC Suivi des phénotypes de S. aureus")

    selected_pheno = st.selectbox("Choisir un phénotype", pheno_df.columns[1:-1])
    df = pheno_df[["Week", selected_pheno]].copy()
    df.columns = ["Week", "R"]
    df["Total"] = pheno_df["MRSA"] + pheno_df["VRSA"] + pheno_df["Wild"] + pheno_df["Other"]

    # Exception pour VRSA ou Vancomycine
    if selected_pheno.lower() in ["vrsa", "vancomycine"]:
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

    if df["outlier"].any():
        st.subheader("\U0001F6A8 Services concernés (Export 2024)")
        export_df.columns = export_df.columns.str.lower()
        alerts = export_df[(export_df["lib_germe"].str.lower().str.contains("staphylococcus aureus", na=False)) &
                           (export_df["libelle demandeur"].notna())]
        st.dataframe(alerts[["date prelevement", "libelle demandeur"]].drop_duplicates())
