import pandas as pd

# ==============================
# MUTUO
# ==============================

def calcola_mutuo_massimo(stipendio, quota_rata, tasso_annuo, anni):
    rata_max = stipendio * quota_rata
    tasso_mensile = (tasso_annuo / 100) / 12
    n_rate = anni * 12
    mutuo_massimo = rata_max * (1 - (1 + tasso_mensile) ** -n_rate) / tasso_mensile
    return mutuo_massimo


def calcola_rata(capitale, tasso_annuo, anni):
    tasso_mensile = (tasso_annuo / 100) / 12
    n_rate = anni * 12
    return capitale * tasso_mensile / (1 - (1 + tasso_mensile) ** -n_rate)


# ==============================
# COMPUTO RISTRUTTURAZIONE
# ==============================

COLONNE_COMPUTO = ["n", "categoria", "lavorazione", "quantita", "um", "prezzo", "codice", "nota"]

# Scenari pensati per il computo della casa che stiamo valutando (numeri di voce di quel documento):
# compaiono solo se il CSV caricato ha quelle voci.
# Le macerie da 40 m3 sono stimate come ~18 m3 di intonaco + ~20 m3 di pavimenti + ~2 m3 di altro.
SCENARI = {
    "intonaco_ok": "L'intonaco esistente è in buono stato (niente spicconatura, intonaco nuovo solo nel sottotetto)",
    "pavimento_ok": "Si posa sopra il pavimento esistente (niente demolizione né massetto)",
    "pittura_mercato": "Pittura a prezzo di mercato (8 €/mq invece di 12)",
}


def carica_computo(file):
    df = pd.read_csv(file)
    mancanti = [c for c in COLONNE_COMPUTO if c not in df.columns]
    if mancanti:
        raise ValueError(f"Nel CSV mancano le colonne: {', '.join(mancanti)}")
    df = df[COLONNE_COMPUTO].copy()
    df["nota"] = df["nota"].fillna("")
    df["codice"] = df["codice"].astype(str)
    df.insert(0, "includi", True)
    return df


def scenari_applicabili(df):
    return set(df["n"]) >= {4, 7, 8, 12, 14, 17, 18}


def applica_scenari(df, scenari):
    df = df.copy()
    righe = df.set_index("n").index

    def imposta(n, colonna, valore):
        if n in righe:
            df.loc[df["n"] == n, colonna] = valore

    macerie_in_meno = 0
    if scenari.get("intonaco_ok"):
        imposta(7, "includi", False)
        imposta(12, "quantita", 100.5)
        macerie_in_meno += 18
    if scenari.get("pavimento_ok"):
        imposta(4, "includi", False)
        imposta(8, "includi", False)
        macerie_in_meno += 20
    if scenari.get("pittura_mercato"):
        imposta(14, "prezzo", 8.0)
    if macerie_in_meno and 17 in righe and 18 in righe:
        m3 = max(2.0, float(df.loc[df["n"] == 17, "quantita"].iloc[0]) - macerie_in_meno)
        imposta(17, "quantita", m3)
        imposta(18, "quantita", m3 * 1800)
    return df


def totale_computo(df):
    importi = df["quantita"] * df["prezzo"] * df["includi"].astype(bool)
    return float(importi.sum())


def totali_per_categoria(df):
    d = df.assign(importo=df["quantita"] * df["prezzo"] * df["includi"].astype(bool))
    return d.groupby("categoria", sort=False)["importo"].sum()


def quantita_da_computo(df):
    """Quantità dei materiali a nostro carico, lette dalle voci di sola posa del computo.
    Se una voce non c'è, resta un valore generico da correggere a mano."""
    def cerca(*parole, default):
        testo = df["lavorazione"].str.lower()
        trovate = df[testo.str.contains("posa") & testo.apply(lambda t: all(p in t for p in parole))]
        return float(trovate["quantita"].sum()) if len(trovate) else default

    return {
        "pavimenti_mq": cerca("pavimenti", default=100.0),
        "rivestimenti_mq": cerca("rivestimenti", default=10.0),
        "battiscopa_m": cerca("battiscopa", default=60.0),
        "n_porte": int(cerca("porte interne", default=5)),
        "n_bagni": 1,
    }


def costi_extra(computo, extra):
    """Costi che il computo non copre. `extra` contiene i valori scelti dall'utente."""
    voci = {
        "Materiali a nostro carico": (
            extra["pavimenti_mq"] * extra["prezzo_pavimenti"]
            + extra["rivestimenti_mq"] * extra["prezzo_rivestimenti"]
            + extra["battiscopa_m"] * extra["prezzo_battiscopa"]
            + extra["n_porte"] * extra["prezzo_porta"]
            + extra["porta_blindata"]
            + extra["n_bagni"] * extra["prezzo_bagno"]
        ),
        "Riscaldamento e clima": extra["riscaldamento"],
        "Finestre: controtelai e davanzali": extra["finestre_extra"],
        "Tecnico, pratiche, sicurezza": computo * extra["tecnici_pct"] / 100,
        "Imprevisti": computo * extra["imprevisti_pct"] / 100,
    }
    return voci


def detrazione(spesa, aliquota_pct, tetto=96000):
    return min(spesa, tetto) * aliquota_pct / 100


# ==============================
# PIANO FINANZIARIO
# ==============================

def piano_finanziario(prezzo, costi_acquisto, lavori, quota_mutuo, lavori_nel_mutuo):
    """Quanto copre il mutuo e quanti contanti servono."""
    base_mutuo = prezzo + (lavori if lavori_nel_mutuo else 0)
    mutuo = quota_mutuo * base_mutuo
    totale = prezzo + costi_acquisto + lavori
    contanti = totale - mutuo
    return {"totale": totale, "mutuo": mutuo, "contanti": contanti}
