Super, je te prépare **le app.py complet**, interactif, pour tous les onglets avec **les bons fichiers**, **grandes polices**, **graphes lisibles**, **moyenne mobile sur 8 semaines**, **IC95%**, **seuil d’alerte** (pointillé rouge + gros points rouges pour alarmes), **filtres par antibio/phenotype**, **tableaux filtrables**.

---

## ⚡️ **Voici le `app.py` complet**  
*(copie tout ce code dans un seul fichier)*

```python
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(layout="wide")
plt.rcParams.update({'font.size': 20, 'axes.labelweight': 'bold', 'axes.titlesize': 24})

def calcul_ic95(prop, n):
    se = np.sqrt(prop * (1 - prop) / n)
    lower = prop - 1.96 * se
    upper = prop + 1.96 * se
    return np.clip(lower*100, 0, 100), np.clip(upper*100, 0, 100)

# ==============================
# CHARGEMENT DES DONNÉES
# ==============================

@st.cache_data
def load_all_data():
    dfs = {}
    # Fichier 2 : Résistance - Tests
    if Path("tests_par_semaine_antibiotiques_2024.csv").exists():
        dfs["tests"] = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    else:
        dfs["tests"] = pd.DataFrame()

    # Fichier 3 : Résistance - Other AB
    if Path("other Antibiotiques staph aureus.xlsx").exists():
        dfs["other"] = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    else:
        dfs["other"] = pd.DataFrame()

    # Fichier 4 : Phénotypes
    if Path("staph_aureus_pheno_final.xlsx").exists():
        dfs["pheno"] = pd.read_excel("staph_aureus_pheno_final.xlsx")
    else:
        dfs["pheno"] = pd.DataFrame()

    # Onglet 1, 5, 6
    if Path("Export_StaphAureus_COMPLET.csv").exists():
        dfs["export"] = pd.read_csv("Export_StaphAureus_COMPLET.csv")
    else:
        dfs["export"] = pd.DataFrame()
    return dfs

dfs = load_all_data()

# ==============================
# ONGLET SETUP
# ==============================

onglet = st.tabs([
    "Toutes les bactéries",
    "Résistance - Tests",
    "Résistance - Other AB",
    "Phénotypes",
    "Tableau Interactif",
    "Alertes par Service"
])

# ==============================
# ONGLET 1 - Toutes les bactéries
# ==============================

with onglet[0]:
    st.header("Toutes les bactéries")
    df = dfs["export"]
    if df.empty:
        st.error("Fichier Export_StaphAureus_COMPLET.csv manquant ou vide.")
    else:
        # Recherche colonne bactéries (exemple : "lib_germe" ou autre)
        bact_col = next((c for c in df.columns if "germe" in c.lower() or "bacterie" in c.lower()), None)
        sem_col = next((c for c in df.columns if "semaine" in c.lower()), None)
        if not bact_col or not sem_col:
            st.error("Colonne de bactérie ou de semaine non trouvée.")
        else:
            semaines = sorted(df[sem_col].dropna().unique())
            semaine_sel = st.select_slider("Filtrer par semaine", options=["Toutes"] + list(semaines))
            if semaine_sel == "Toutes":
                plotdf = df
            else:
                plotdf = df[df[sem_col] == semaine_sel]
            counts = plotdf[bact_col].value_counts().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(counts.index, counts.values, color="steelblue")
            ax.set_ylabel("Nombre d'isolats", fontsize=20, fontweight="bold")
            ax.set_xlabel("Bactérie", fontsize=20, fontweight="bold")
            ax.set_title(f"Nombre d'isolats par bactérie (Semaine {semaine_sel})", fontsize=24, fontweight="bold")
            ax.tick_params(axis='x', rotation=25)
            for i, v in enumerate(counts.values):
                ax.text(i, v + 1, str(v), ha='center', va='bottom', fontsize=18, fontweight='bold')
            st.pyplot(fig)

# ==============================
# ONGLET 2 - Résistance - Tests
# ==============================

with onglet[1]:
    st.header("Évolution % Résistance par antibiotique (tests principaux)")
    df = dfs["tests"]
    if df.empty:
        st.error("Fichier tests_par_semaine_antibiotiques_2024.csv manquant ou vide.")
    else:
        antibio_list = [col for col in df.columns if col not in ['semaine', 'N']]
        antibio = st.selectbox("Choisir l'antibiotique", antibio_list)
        seuil = st.slider("Seuil d'alerte (%)", 0, 100, 50)
        df = df.dropna(subset=[antibio])
        df = df[df["N"] > 0]
        df["%res"] = df[antibio] / df["N"] * 100
        window = 8
        df["rolling"] = df["%res"].rolling(window=window, min_periods=1).mean()
        df["ic95_low"], df["ic95_high"] = zip(*[calcul_ic95(row[antibio]/row["N"], row["N"]) for idx, row in df.iterrows()])
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.plot(df["semaine"], df["%res"], 'o-', label='% Résistance', color="crimson", linewidth=4)
        ax.plot(df["semaine"], df["rolling"], 'b-', label=f'Moy. mobile ({window} sem)', linewidth=4)
        ax.fill_between(df["semaine"], df["ic95_low"], df["ic95_high"], color='gray', alpha=0.3, label="IC95%")
        ax.axhline(seuil, color='red', linestyle='--', linewidth=3, label="Seuil Alerte")
        alertes = df[df["rolling"] >= seuil]
        ax.scatter(alertes["semaine"], alertes["rolling"], s=400, color="darkred", alpha=0.7, marker='o', edgecolors='black', zorder=5)
        ax.set_xlabel("Semaine", fontsize=20, fontweight='bold')
        ax.set_ylabel("% Résistance", fontsize=20, fontweight='bold')
        ax.set_title(f"Évolution de la résistance à {antibio}", fontsize=24, fontweight='bold')
        ax.legend(fontsize=16)
        ax.grid(True, linewidth=1)
        st.pyplot(fig)

# ==============================
# ONGLET 3 - Résistance - Other AB
# ==============================

with onglet[2]:
    st.header("Évolution % Résistance par antibiotique (other AB)")
    df = dfs["other"]
    if df.empty:
        st.error("Fichier other Antibiotiques staph aureus.xlsx manquant ou vide.")
    else:
        ab_cols = [col for col in df.columns if col not in ['semaine', 'N']]
        antibio2 = st.selectbox("Choisir l'antibiotique (Other AB)", ab_cols)
        seuil2 = st.slider("Seuil d'alerte (%)", 0, 100, 50, key="seuil2")
        df = df.dropna(subset=[antibio2])
        df = df[df["N"] > 0]
        df["%res"] = df[antibio2] / df["N"] * 100
        window = 8
        df["rolling"] = df["%res"].rolling(window=window, min_periods=1).mean()
        df["ic95_low"], df["ic95_high"] = zip(*[calcul_ic95(row[antibio2]/row["N"], row["N"]) for idx, row in df.iterrows()])
        fig2, ax2 = plt.subplots(figsize=(11, 6))
        ax2.plot(df["semaine"], df["%res"], 'o-', label='% Résistance', color="crimson", linewidth=4)
        ax2.plot(df["semaine"], df["rolling"], 'b-', label=f'Moy. mobile ({window} sem)', linewidth=4)
        ax2.fill_between(df["semaine"], df["ic95_low"], df["ic95_high"], color='gray', alpha=0.3, label="IC95%")
        ax2.axhline(seuil2, color='red', linestyle='--', linewidth=3, label="Seuil Alerte")
        alertes2 = df[df["rolling"] >= seuil2]
        ax2.scatter(alertes2["semaine"], alertes2["rolling"], s=400, color="darkred", alpha=0.7, marker='o', edgecolors='black', zorder=5)
        ax2.set_xlabel("Semaine", fontsize=20, fontweight='bold')
        ax2.set_ylabel("% Résistance", fontsize=20, fontweight='bold')
        ax2.set_title(f"Évolution de la résistance à {antibio2}", fontsize=24, fontweight='bold')
        ax2.legend(fontsize=16)
        ax2.grid(True, linewidth=1)
        st.pyplot(fig2)

# ==============================
# ONGLET 4 - Phénotypes
# ==============================

with onglet[3]:
    st.header("Évolution % de chaque phénotype")
    df = dfs["pheno"]
    if df.empty:
        st.error("Fichier staph_aureus_pheno_final.xlsx manquant ou vide.")
    else:
        pheno_cols = [col for col in df.columns if col not in ['semaine', 'N']]
        phenotype = st.selectbox("Choisir le phénotype", pheno_cols)
        seuil_p = st.slider("Seuil d'alerte (%)", 0, 100, 50, key="seuil_pheno")
        df = df.dropna(subset=[phenotype])
        df = df[df["N"] > 0]
        df["%pheno"] = df[phenotype] / df["N"] * 100
        window = 8
        df["rolling"] = df["%pheno"].rolling(window=window, min_periods=1).mean()
        df["ic95_low"], df["ic95_high"] = zip(*[calcul_ic95(row[phenotype]/row["N"], row["N"]) for idx, row in df.iterrows()])
        fig3, ax3 = plt.subplots(figsize=(11, 6))
        ax3.plot(df["semaine"], df["%pheno"], 'o-', label='% Phénotype', color="crimson", linewidth=4)
        ax3.plot(df["semaine"], df["rolling"], 'b-', label=f'Moy. mobile ({window} sem)', linewidth=4)
        ax3.fill_between(df["semaine"], df["ic95_low"], df["ic95_high"], color='gray', alpha=0.3, label="IC95%")
        ax3.axhline(seuil_p, color='red', linestyle='--', linewidth=3, label="Seuil Alerte")
        alertes3 = df[df["rolling"] >= seuil_p]
        ax3.scatter(alertes3["semaine"], alertes3["rolling"], s=400, color="darkred", alpha=0.7, marker='o', edgecolors='black', zorder=5)
        ax3.set_xlabel("Semaine", fontsize=20, fontweight='bold')
        ax3.set_ylabel("% Phénotype", fontsize=20, fontweight='bold')
        ax3.set_title(f"Évolution du phénotype {phenotype}", fontsize=24, fontweight='bold')
        ax3.legend(fontsize=16)
        ax3.grid(True, linewidth=1)
        st.pyplot(fig3)

# ==============================
# ONGLET 5 - Tableau Interactif
# ==============================

with onglet[4]:
    st.header("Exploration Interactive")
    df = dfs["export"]
    if df.empty:
        st.error("Fichier Export_StaphAureus_COMPLET.csv manquant ou vide.")
    else:
        st.dataframe(df)

# ==============================
# ONGLET 6 - Alertes par Service
# ==============================

with onglet[5]:
    st.header("\U0001F6A8 Services concernés par des alertes")
    df = dfs["export"]
    if df.empty:
        st.error("Fichier Export_StaphAureus_COMPLET.csv manquant ou vide.")
    else:
        # Recherche automatique des colonnes
        col_uf = next((col for col in df.columns if "uf" in col.lower()), None)
        col_germe = next((col for col in df.columns if "germe" in col.lower()), None)
        col_alerte = next((col for col in df.columns if "alerte" in col.lower()), None)
        col_semaine = next((col for col in df.columns if "semaine" in col.lower()), None)
        if None in [col_uf, col_germe, col_alerte, col_semaine]:
            st.error("Colonnes requises manquantes dans export_df. Vérifiez les noms.")
        else:
            semaines = sorted(df[col_semaine].dropna().unique())
            semaine_selectionnee = st.selectbox("Semaine avec alerte", semaines)
            subset = df[df[col_semaine] == semaine_selectionnee][[col_uf, col_germe, col_alerte]].drop_duplicates()
            if not subset.empty:
                st.write(f"Alertes pour la semaine {semaine_selectionnee} :")
                st.dataframe(subset)
            else:
                st.info(f"Aucune alerte trouvée pour la semaine {semaine_selectionnee}.")
```

---

### **Ce que fait ce code :**

- **Onglet 1** : Bar chart isolats/bactérie, filtrable par semaine
- **Onglet 2/3/4** : Graphique par AB ou phénotype choisi, très visible, gros, police bold, seuil, IC95%, alertes en gros points rouges
- **Onglet 5** : Tableau interactif complet
- **Onglet 6** : Tableau alertes par service, filtré par semaine

**Utilise bien les fichiers avec les noms donnés** dans le même dossier que ton app !

---

**Si tu veux que j’adapte les noms de colonnes automatiquement à ce que tu as exactement dans tes fichiers, envoie un exemple de chaque fichier (juste l’en-tête) !**

Essaie ce script, et tu vas voir : c’est ultra lisible, interactif, bold et dynamique en temps réel !

---

Dis-moi si tu veux encore plus de personnalisation ! 😎
