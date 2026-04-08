# modele.py
import pandas as pd
import numpy as np
from pipeline import (normalize_name, label_minutes,
                      COLS_INVERSES_EQUIPES, COLS_INVERSES_JOUEURS)

LIGUES = ["L1", "L2", "Liga", "Liga_seg"]

# ============================================================
# COLONNES ÉQUIPES
# ============================================================

COLS_EQUIPES = {
    "Possession, %":                     "possession",
    "PPDA":                              "ppda",
    "xG":                                "xg",
    "Tirs / cadrés":                     "tirs_total",
    "Unnamed: 8":                        "tirs_cadres",
    "Unnamed: 9":                        "tirs_cadres_pct",
    "Passes / précises":                 "passes_total",
    "Unnamed: 11":                       "passes_precises",
    "Unnamed: 12":                       "passes_precises_pct",
    "Pertes/Bas/Moyen/Élevé":           "pertes_total",
    "Unnamed: 15":                       "pertes_bas",
    "Unnamed: 16":                       "pertes_moyen",
    "Unnamed: 17":                       "pertes_eleve",
    "Récupérations/Bas/Moyen/Élevé":    "recup_total",
    "Unnamed: 19":                       "recup_bas",
    "Unnamed: 20":                       "recup_moyen",
    "Unnamed: 21":                       "recup_eleve",
    "Contre-attaques/avec tirs":         "contre_attaques",
    "Unnamed: 32":                       "contre_attaques_tirs",
    "Passes en profondeur terminées":    "passes_profondeur",
    "Interceptions":                     "interceptions",
    "Passes progressives/précises":      "passes_progressives_total",
    "Unnamed: 93":                       "passes_progressives_precises",
    "Passes dans 3ème tiers / précises": "passes_3eme_tiers_total",
    "% passes longues":                  "pct_passes_longues",
    "Attaques positionnelles/avec tirs": "attaques_positionnelles",
    "Unnamed: 29":                       "attaques_positionnelles_tirs",
    "Entrées dans la la surface de réparation (courses/centres)": "entrees_surface",
    "Duels défensifs / gagnés":          "duels_def_total",
    "Unnamed: 64":                       "duels_def_gagnes",
    "Unnamed: 65":                       "duels_def_gagnes_pct",
    "Tacles glissés/réussis":            "tacles_total",
    "Buts concédés":                     "buts_concedes",
    "Fautes":                            "fautes",
    "Cartons jaunes":                    "cartons_jaunes",
    "Cartons rouges":                    "cartons_rouges",
    "Hors-jeu":                          "hors_jeu",
}

# ============================================================
# NORMALISATION ÉQUIPES — intra-ligue
# ============================================================

def normaliser_equipes(df_teams: pd.DataFrame) -> pd.DataFrame:
    cols_num = [
        c for c in df_teams.columns
        if df_teams[c].dtype in ["float64", "int64"]
    ]

    blocs = []
    for ligue in LIGUES:
        mask = df_teams["Ligue"] == ligue
        sub  = df_teams.loc[mask, cols_num].copy()
        normed = {}
        for col in cols_num:
            vals = sub[col]
            if col in COLS_INVERSES_EQUIPES:
                normed[col] = (1 - vals.rank(pct=True)) * 100
            else:
                normed[col] = vals.rank(pct=True) * 100
        bloc = pd.DataFrame(normed, index=sub.index)
        bloc["Ligue"]       = ligue
        bloc["Equipe"]      = df_teams.loc[mask, "Equipe"].values
        bloc["equipe_norm"] = df_teams.loc[mask, "equipe_norm"].values
        blocs.append(bloc)

    df_norm = pd.concat(blocs, ignore_index=True)

    # ── SANS BALLON — Bloc ────────────────────────────────────
    # Où l'équipe récupère le ballon = hauteur du bloc
    # recup_eleve inversé car dans COLS_INVERSES → on le réinverse ici
    # On veut : recup_eleve élevé = bloc haut = score élevé
    total_recup = (
        df_norm["recup_eleve"] +
        df_norm["recup_moyen"] +
        df_norm["recup_bas"]
    ).replace(0, np.nan)

    df_norm["score_bloc"] = (
        (df_norm["recup_eleve"] / total_recup * 100) * 0.50 +
        (df_norm["recup_moyen"] / total_recup * 100) * 0.30 +
        ((100 - df_norm["recup_bas"]) / 100 * 100) * 0.20
    )

    # ── SANS BALLON — Pressing ────────────────────────────────
    # ppda déjà inversé (bas = intense = score élevé)
    df_norm["score_pressing"] = (
        df_norm["ppda"]          * 0.40 +
        df_norm["tacles_total"]  * 0.25 +
        df_norm["interceptions"] * 0.25 +
        df_norm["duels_def_total"] * 0.10
    )

    # ── AVEC BALLON — Style de jeu ────────────────────────────
    # pct_passes_longues inversé dans COLS_INVERSES
    # → score élevé = jeu court = possession
    df_norm["score_avec_ballon"] = (
        df_norm["possession"]                * 0.30 +
        df_norm["passes_progressives_total"] * 0.30 +
        df_norm["pct_passes_longues"]        * 0.25 +
        df_norm["passes_3eme_tiers_total"]   * 0.15
    )

    # ── TRANSITION OFFENSIVE ──────────────────────────────────
    # Fréquence des transitions — pas l'efficacité
    df_norm["score_transition_off"] = (
        df_norm["contre_attaques"]   * 0.60 +
        df_norm["passes_profondeur"] * 0.40
    )

    # ── LABELS ───────────────────────────────────────────────
    df_norm["label_bloc"] = df_norm["score_bloc"].apply(_label_bloc)
    df_norm["label_pressing"] = df_norm["score_pressing"].apply(_label_pressing)
    df_norm["label_avec_ballon"] = df_norm["score_avec_ballon"].apply(_label_avec_ballon)
    df_norm["label_transition_off"] = df_norm["score_transition_off"].apply(_label_transition_off)

    return df_norm


# ============================================================
# JOUEURS — normalisation + ajustement contextuel
# ============================================================

def build_df_final(df_players: pd.DataFrame,
                   df_norm: pd.DataFrame) -> pd.DataFrame:

    cols_stats = _STATS_COLS()
    cols_stats = [c for c in cols_stats if c in df_players.columns]

    # Percentiles intra-ligue
    blocs = []
    for ligue in LIGUES:
        mask = df_players["ligue"] == ligue
        sub  = df_players.loc[mask, cols_stats].copy()
        normed = {}
        for col in cols_stats:
            vals = pd.to_numeric(sub[col], errors="coerce")
            if col in COLS_INVERSES_JOUEURS:
                normed[col] = (1 - vals.rank(pct=True)) * 100
            else:
                normed[col] = vals.rank(pct=True) * 100
        blocs.append(pd.DataFrame(normed, index=sub.index))

    df_players_norm = pd.concat(blocs).reindex(df_players.index)

    # Jointure joueur × style équipe
    cols_style = [
        "equipe_norm",
        "score_bloc", "score_pressing",
        "score_avec_ballon", "score_transition_off",
        "label_bloc", "label_pressing",
        "label_avec_ballon", "label_transition_off",
    ]
    df_ctx = df_players.merge(
        df_norm[cols_style], on="equipe_norm", how="left"
    )

    # ── Ajustement contextuel ─────────────────────────────────
    # Stats défensives → corrigées par score_pressing
    for col in ["actions_def_90", "duels_def_90", "tacles_padj",
                "interceptions_padj", "tirs_contres_90"]:
        if col in df_ctx.columns:
            f = _facteur(df_ctx["score_pressing"].fillna(50))
            df_ctx[f"{col}_adj"] = df_ctx[col] * f

    # Stats de passes → corrigées par score_avec_ballon
    for col in ["passes_90", "passes_pct", "passes_prog_90",
                "passes_avant_90", "passes_tiers_adv_90"]:
        if col in df_ctx.columns:
            f = _facteur(df_ctx["score_avec_ballon"].fillna(50))
            df_ctx[f"{col}_adj"] = df_ctx[col] * f

    # Stats de transition → corrigées par score_transition_off
    for col in ["courses_prog_90", "accelerations_90", "dribbles_90"]:
        if col in df_ctx.columns:
            f = _facteur(df_ctx["score_transition_off"].fillna(50))
            df_ctx[f"{col}_adj"] = df_ctx[col] * f

    # Percentiles inter-ligues sur stats ajustées
    cols_adj = [c for c in df_ctx.columns if c.endswith("_adj")]
    cols_off = ["xg_90", "xa_90", "secondes_pd_90",
                "passes_quasi_pd_90", "passes_surface_90",
                "passes_penetrantes_90", "passes_judicieuses_90"]

    cols_pct_map = {}
    for col in cols_adj + cols_off:
        if col in df_ctx.columns:
            vals = pd.to_numeric(df_ctx[col], errors="coerce")
            cols_pct_map[col + "_pct"] = vals.rank(pct=True) * 100

    df_final = pd.concat(
        [df_ctx, pd.DataFrame(cols_pct_map, index=df_ctx.index)],
        axis=1
    )

    # ── 6 PROFILS MC ─────────────────────────────────────────
    df_final["score_mc_recuperateur"] = _score_profil(df_final, "recuperateur")
    df_final["score_mc_mdef"]         = _score_profil(df_final, "mdef")
    df_final["score_mc_relanceur"]    = _score_profil(df_final, "relanceur")
    df_final["score_mc_boxtbox"]      = _score_profil(df_final, "boxtbox")
    df_final["score_mc_interieur"]    = _score_profil(df_final, "interieur")
    df_final["score_mc_offensif"]     = _score_profil(df_final, "offensif")

    # Impact contexte
    impact_cols = ["interceptions_padj", "tacles_padj",
                   "passes_prog_90", "passes_pct"]
    deltas = []
    for col in impact_cols:
        if col in df_final.columns and f"{col}_adj" in df_final.columns:
            d = ((df_final[f"{col}_adj"] - df_final[col]) /
                 df_final[col].replace(0, np.nan))
            deltas.append(d)
    df_final["impact_contexte"] = pd.concat(deltas, axis=1).mean(axis=1)

    # Fiabilité
    df_final["niveau_fiabilite"] = df_final["minutes"].apply(label_minutes)

    return df_final


# ============================================================
# HELPERS
# ============================================================

def _facteur(score, neutre=50, amplitude=0.30):
    """
    Correction contextuelle avec amplitude progressive.
    
    Logique : moins on corrige aux extrêmes (PSG, équipes très basses),
    plus on corrige au centre (équipes dans la moyenne).
    
    - Score proche de 50 (équipe normale) → correction forte jusqu'à ±30%
    - Score très éloigné de 50 (PSG, équipe très basse) → correction réduite
    """
    # Distance normalisée 0→1 (0 = proche du centre, 1 = extrême)
    distance = abs(score - neutre) / neutre
    
    # Amplitude progressive — réduite aux extrêmes
    # distance=0 → amplitude pleine (0.30)
    # distance=1 → amplitude réduite de moitié (0.15)
    amplitude_adj = amplitude * (1 - 0.5 * distance)
    
    facteur = 1 + amplitude_adj * (neutre - score) / neutre
    return facteur.clip(1 - amplitude, 1 + amplitude)

def _STATS_COLS():
    from pipeline import COLS_JOUEURS
    return list(COLS_JOUEURS.values())

def _score_moyen(df, cols):
    cols_pct = [c + "_pct" for c in cols if c + "_pct" in df.columns]
    if not cols_pct:
        return pd.Series(0.0, index=df.index)
    return df[cols_pct].mean(axis=1)

def _score_profil(df, profil):
    adj_def    = ["actions_def_90_adj", "duels_def_90_adj",
                  "tacles_padj_adj", "interceptions_padj_adj",
                  "tirs_contres_90_adj"]
    adj_passes = ["passes_90_adj", "passes_pct_adj",
                  "passes_prog_90_adj", "passes_avant_90_adj",
                  "passes_tiers_adv_90_adj"]
    adj_trans  = ["courses_prog_90_adj", "accelerations_90_adj",
                  "dribbles_90_adj"]
    offensif   = ["xg_90", "xa_90", "secondes_pd_90",
                  "passes_quasi_pd_90", "passes_surface_90"]
    interieur  = ["passes_penetrantes_90", "passes_judicieuses_90",
                  "xa_90", "passes_quasi_pd_90", "dribbles_90"]
    pressing_i = ["actions_def_90_adj", "tirs_contres_90_adj",
                  "duels_def_pct", "duels_aeriens_pct"]

    if profil == "recuperateur":
        # Défend + récupère + relance simple
        return (_score_moyen(df, adj_def)    * 0.55 +
                _score_moyen(df, pressing_i) * 0.25 +
                _score_moyen(df, adj_passes) * 0.20)

    elif profil == "mdef":
        # Défend + donne simple + ne prend pas de risques
        # Peu de passes progressives, beaucoup de passes sûres
        return (_score_moyen(df, adj_def)    * 0.65 +
                _score_moyen(df, pressing_i) * 0.25 +
                _score_moyen(df, ["passes_pct_adj"]) * 0.10)

    elif profil == "relanceur":
        # Relance + passes progressives + peu défensif
        return (_score_moyen(df, adj_passes) * 0.55 +
                _score_moyen(df, adj_def)    * 0.20 +
                _score_moyen(df, offensif)   * 0.25)

    elif profil == "boxtbox":
        # Équilibré défense + passes + transition
        return (_score_moyen(df, adj_def)    * 0.30 +
                _score_moyen(df, adj_passes) * 0.30 +
                _score_moyen(df, adj_trans)  * 0.20 +
                _score_moyen(df, offensif)   * 0.20)

    elif profil == "interieur":
        # Passes entre les lignes + dribbles + xA + passes pénétrantes
        # Style Pedri / Vitinha / Joao Neves
        return (_score_moyen(df, interieur)  * 0.50 +
                _score_moyen(df, adj_passes) * 0.30 +
                _score_moyen(df, adj_trans)  * 0.20)

    elif profil == "offensif":
        # xG + xA + passes surface + contribution offensive
        return (_score_moyen(df, offensif)   * 0.55 +
                _score_moyen(df, adj_passes) * 0.25 +
                _score_moyen(df, adj_trans)  * 0.20)

    return pd.Series(0.0, index=df.index)


# ── Labels ────────────────────────────────────────────────────

def _label_bloc(x):
    if x >= 66:   return "Bloc haut"
    elif x >= 33: return "Bloc médian"
    else:         return "Bloc bas"

def _label_pressing(x):
    if x >= 66:   return "Pressing intensif"
    elif x >= 33: return "Pressing modéré"
    else:         return "Bloc passif"

def _label_avec_ballon(x):
    if x >= 66:   return "Possession"
    elif x >= 33: return "Équilibré"
    else:         return "Jeu direct"

def _label_transition_off(x):
    if x >= 66:   return "Contre-attaque"
    elif x >= 33: return "Mixte"
    else:         return "Jeu placé"


    