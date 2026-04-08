# pipeline.py
import pandas as pd
import numpy as np
import unicodedata
import os

# ============================================================
# CONSTANTES
# ============================================================

COLS_INVERSES_EQUIPES = [
    "ppda", "pct_passes_longues", "pertes_total",
    "recup_bas", "buts_concedes", "fautes",
    "cartons_jaunes", "cartons_rouges", "hors_jeu",
]

COLS_INVERSES_JOUEURS = ["fautes_90"]

COLS_JOUEURS = {
    "Actions défensives réussies par 90": "actions_def_90",
    "Duels défensifs par 90":             "duels_def_90",
    "Duels défensifs gagnés, %":          "duels_def_pct",
    "Duels aériens par 90":               "duels_aeriens_90",
    "Duels aériens gagnés, %":            "duels_aeriens_pct",
    "Tacles glissés PAdj":                "tacles_padj",
    "Tirs contrés par 90":                "tirs_contres_90",
    "Interceptions PAdj":                 "interceptions_padj",
    "Fautes par 90":                      "fautes_90",
    "xG par 90":                          "xg_90",
    "Tirs par 90":                        "tirs_90",
    "Tirs à la cible, %":                 "tirs_cible_pct",
    "Dribbles par 90":                    "dribbles_90",
    "Dribbles réussis, %":                "dribbles_pct",
    "Duels offensifs par 90":             "duels_off_90",
    "Courses progressives par 90":        "courses_prog_90",
    "Accélérations par 90":               "accelerations_90",
    "Fautes subies par 90":               "fautes_subies_90",
    "Passes par 90":                      "passes_90",
    "Passes précises, %":                 "passes_pct",
    "Passes avant par 90":                "passes_avant_90",
    "Passes en avant précises, %":        "passes_avant_pct",
    "Passes longues par 90":              "passes_longues_90",
    "Longues passes précises, %":         "passes_longues_pct",
    "xA par 90":                          "xa_90",
    "Secondes passes décisives par 90":   "secondes_pd_90",
    "Passes judicieuses par 90":          "passes_judicieuses_90",
    "Passes quasi décisives par 90":      "passes_quasi_pd_90",
    "Passes dans tiers adverse par 90":   "passes_tiers_adv_90",
    "Passes dans tiers adverse précises, %": "passes_tiers_adv_pct",
    "Passes vers la surface de réparation par 90": "passes_surface_90",
    "Passes vers la surface de réparation précises, %": "passes_surface_pct",
    "Passes pénétrantes par 90":          "passes_penetrantes_90",
    "Passes progressives par 90":         "passes_prog_90",
    "Passes progressives précises, %":    "passes_prog_pct",
}

COLS_IDENTITE_JOUEURS = {
    "Joueur":    "joueur",
    "Équipe":    "equipe",
    "Équipe dans la période sélectionnée": "equipe_periode",
    "Place":     "poste",
    "Âge":       "age",
    "Minutes jouées": "minutes",
    "Pays de naissance": "pays_naissance",
    "Passeport pays": "passeport",
    "Pied":      "pied",
    "Taille":    "taille",
    "Poids":     "poids",
    "Prêté":     "prete",
    "Valeur marchande": "valeur_marchande",
    "Contrat expiration": "contrat",
}

# ============================================================
# UTILITAIRES
# ============================================================

def normalize_name(name):
    if not isinstance(name, str):
        return name
    return unicodedata.normalize("NFC", name.strip().lower())

def label_minutes(mins):
    if mins >= 2000:   return "titulaire"
    elif mins >= 1000: return "rotation"
    elif mins >= 500:  return "echantillon_moyen"
    else:              return "faible_echantillon"

# ============================================================
# MODE DÉMO — chargement CSV pré-calculé
# ============================================================

def load_demo(csv_path: str) -> pd.DataFrame:
    """Charge le CSV pré-calculé depuis Colab."""
    df = pd.read_csv(csv_path)
    return df

# ============================================================
# MODE CUSTOM — pipeline complet depuis exports Wyscout
# ============================================================

def load_teams(uploaded_files: dict) -> pd.DataFrame:
    """
    uploaded_files : dict {ligue: [fichiers xlsx uploadés]}
    Retourne df_teams avec colonnes renommées et nettoyées.
    """
    from modele import COLS_EQUIPES
    dfs = []
    for ligue, files in uploaded_files.items():
        for file in files:
            df     = pd.read_excel(file, header=0, skiprows=[1])
            num    = df.select_dtypes(include="number").columns
            avg    = df[num].mean()
            name   = os.path.basename(file.name) \
                       .replace("Team Stats ", "") \
                       .replace(".xlsx", "") \
                       .replace(" (1)", "").strip()
            avg["Equipe"] = name
            avg["Ligue"]  = ligue
            dfs.append(avg)

    df_teams = pd.DataFrame(dfs)
    df_teams = df_teams.rename(columns=COLS_EQUIPES)
    df_teams = _clean_numeric(df_teams, exclude=["Equipe", "Ligue"])
    df_teams["equipe_norm"] = df_teams["Equipe"].apply(normalize_name)
    return df_teams


def load_players(uploaded_files: dict) -> pd.DataFrame:
    """
    uploaded_files : dict {ligue: fichier xlsx uploadé}
    Retourne df_players avec colonnes renommées.
    """
    dfs = []
    for ligue, file in uploaded_files.items():
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        df["ligue"] = ligue
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    df = df.rename(columns={**COLS_IDENTITE_JOUEURS, **COLS_JOUEURS})
    df["equipe_norm"] = df["equipe_periode"].apply(normalize_name)
    df["minutes"]     = pd.to_numeric(df["minutes"], errors="coerce")
    return df


def _clean_numeric(df, exclude=None):
    exclude = exclude or []
    df = df.copy()
    for col in df.columns:
        if col in exclude:
            continue
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace("%", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
    