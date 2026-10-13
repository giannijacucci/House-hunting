import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
from matplotlib.ticker import MaxNLocator, FuncFormatter
import streamlit as st

from calcoli import (
    calcola_mutuo_massimo, calcola_rata,
    carica_computo, scenari_applicabili, applica_scenari, SCENARI,
    totale_computo, totali_per_categoria, quantita_da_computo, costi_extra, detrazione,
    piano_finanziario,
)

# ---------- STYLING ----------
def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5))

matplotlib.rcParams['font.sans-serif'] = 'Palatino'
mpl.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['mathtext.rm'] = 'Palatino'
matplotlib.rcParams['mathtext.it'] = 'Palatino:italic'
matplotlib.rcParams['mathtext.bf'] = 'Palatino:bold'
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['font.size'] = 7
mpl.rcParams['path.simplify'] = False

axis_width = 1

colorPink   = hex_to_rgb('#FD57E7')
colorOrange = hex_to_rgb('#F4D40C')
colorGreen  = hex_to_rgb('#7FF64D')
colorGrey   = hex_to_rgb('#A9A9A9')
colorLight  = hex_to_rgb('#D3D3D3')
colorRed    = hex_to_rgb('#E34948')

euro = FuncFormatter(lambda x, _: f"€ {x/1000:,.0f}k")

MODELLO_CSV = (
    "n,categoria,lavorazione,quantita,um,prezzo,codice,nota\n"
    "1,Demolizioni e rimozioni,Esempio: demolizione pavimenti,100,mq,16.5,,\n"
    "2,\"Massetti, pavimenti, rivestimenti\",Esempio: posa pavimenti (forniti da noi),100,mq,30,,Solo posa\n"
)


def stile_assi(ax):
    for spine in ax.spines.values():
        spine.set_linewidth(axis_width)
    ax.tick_params(width=axis_width)


# ==============================
# FIGURE
# ==============================

def fig_mutuo_vs_tasso(stipendio, anni, quota_mutuo, quota_rata,
                       tasso_min, tasso_max):
    tassi = np.linspace(tasso_min, tasso_max, 200)
    mutui = []
    immobili = []

    for t in tassi:
        mutuo_massimo = calcola_mutuo_massimo(stipendio, quota_rata, t, anni)
        valore_immobile = mutuo_massimo / quota_mutuo
        mutui.append(mutuo_massimo)
        immobili.append(valore_immobile)

    mutui = np.array(mutui)
    immobili = np.array(immobili)

    fig, ax = plt.subplots(figsize=(3.5, 2.5), dpi=200)
    ax.plot(tassi, mutui,    label="Mutuo massimo ottenibile",  color=colorGreen)
    ax.plot(tassi, immobili, label="Valore massimo immobile",   color=colorOrange)

    ax.set_xlabel("Tasso di interesse annuo (%)")
    ax.set_ylabel("Valore (€)")
    ax.grid(alpha=0.3)
    ax.legend()

    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    stile_assi(ax)

    fig.tight_layout()
    return fig, tassi, mutui, immobili


def fig_anticipo_vs_valore(valore_max_immobile, quota_anticipo,
                           tasso_fisso, anni, anticipo_max):
    valori_immobile = np.linspace(0, valore_max_immobile, 200)
    anticipi = quota_anticipo * valori_immobile

    fig, ax = plt.subplots(figsize=(3.5, 2.5), dpi=200)
    ax.plot(
        valori_immobile,
        anticipi,
        color=colorPink,
        label=f"Anticipo richiesto (tasso = {tasso_fisso:.1f}%)"
    )

    ax.axhline(
        anticipo_max,
        linestyle=":",
        linewidth=1.2,
        color='k',
        label=f"Anticipo massimo previsto = € {anticipo_max:,.0f}"
    )

    ax.set_xlabel("Valore immobile (€)")
    ax.set_ylabel("Anticipo richiesto (€)")
    ax.grid(alpha=0.3)
    ax.legend()

    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    stile_assi(ax)

    fig.tight_layout()
    return fig


def fig_lavori_per_voce(voci, n_computo):
    """Barre orizzontali: voci del computo in rosa, voci fuori computo in grigio."""
    nomi = list(voci.keys())[::-1]
    valori = list(voci.values())[::-1]
    colori = [colorPink if i >= len(nomi) - n_computo else colorGrey for i in range(len(nomi))]

    fig, ax = plt.subplots(figsize=(3.5, 0.22 * len(nomi) + 0.6), dpi=200)
    barre = ax.barh(nomi, valori, color=colori, height=0.6)
    for b, v in zip(barre, valori):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f" € {v:,.0f}",
                va="center", fontsize=5.5)
    ax.set_xlim(0, max(valori) * 1.3 if valori else 1)
    ax.xaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.grid(alpha=0.3, axis="x")
    ax.tick_params(axis="y", labelsize=6)
    stile_assi(ax)
    fig.tight_layout()
    return fig


def fig_copertura(prezzo, costi_acquisto, lavori, mutuo, risparmi_usati, mancano):
    """Due barre impilate: quanto costa tutto e come lo paghiamo."""
    fig, ax = plt.subplots(figsize=(3.5, 1.5), dpi=200)
    costi = [("Prezzo casa", prezzo, colorGrey),
             ("Costi di acquisto", costi_acquisto, colorLight),
             ("Lavori", lavori, colorPink)]
    coperture = [("Mutuo", mutuo, colorGreen),
                 ("Risparmi", risparmi_usati, colorOrange)]
    if mancano > 0:
        coperture.append(("Mancano", mancano, colorRed))

    for y, segmenti in ((1, costi), (0, coperture)):
        sinistra = 0
        for nome, valore, colore in segmenti:
            hatch = "////" if nome == "Mancano" else None
            ax.barh(y, valore, left=sinistra, color=colore, height=0.55,
                    edgecolor="white", linewidth=0.8, hatch=hatch, label=nome)
            sinistra += valore

    ax.set_yticks([1, 0])
    ax.set_yticklabels(["Quanto costa", "Come paghiamo"])
    ax.xaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.grid(alpha=0.3, axis="x")
    ax.legend(ncol=3, fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.3), frameon=False)
    stile_assi(ax)
    fig.tight_layout()
    return fig


def fig_rata_nel_tempo(rata, rata_massima, detrazione_annua, anni):
    """Rata mensile negli anni: la detrazione la alleggerisce per i primi 10."""
    t = np.arange(0, anni + 1)
    t_detr = t[t <= min(10, anni)]

    fig, ax = plt.subplots(figsize=(3.5, 2.0), dpi=200)
    ax.plot(t, np.full_like(t, rata, dtype=float), color=colorGreen,
            label=f"Rata del mutuo = € {rata:,.0f}")
    if detrazione_annua > 0:
        ax.plot(t_detr, np.full_like(t_detr, rata - detrazione_annua / 12, dtype=float), color=colorPink,
                label=f"Rata meno la detrazione (primi 10 anni) = € {rata - detrazione_annua / 12:,.0f}")
    ax.axhline(rata_massima, linestyle=":", linewidth=1.2, color="k",
               label=f"Rata massima sostenibile = € {rata_massima:,.0f}")
    ax.set_xlabel("Anni")
    ax.set_ylabel("€ al mese")
    ax.set_ylim(0, max(rata, rata_massima) * 1.25)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=5.5)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    stile_assi(ax)
    fig.tight_layout()
    return fig


# ==============================
# APP STREAMLIT
# ==============================

st.set_page_config(page_title="Mutuo & Casa", page_icon="🏠", layout="centered")

st.title("🏠 Case a prima vista")

st.markdown(
    "Strumentino per capire **cosa possiamo permetterci** "
    "in base allo stipendio, al tasso e all'anticipo.\n\n"
    "⚠️ *Il file è interattivo: tutti i valori possono essere modificati direttamente in questa pagina.*"
)

# --- Sidebar parametri base ---
st.sidebar.header("Parametri di base")

stipendio = st.sidebar.number_input("Stipendio mensile netto (€)", min_value=500, max_value=20000, value=4000, step=100)
anni = st.sidebar.slider("Durata mutuo (anni)", min_value=5, max_value=40, value=30)
quota_rata = st.sidebar.slider("Quota massima rata / stipendio", min_value=0.1, max_value=0.5, value=1/3, step=0.01)
quota_mutuo = st.sidebar.slider("Percentuale mutuo rispetto al valore casa", min_value=0.5, max_value=1.0, value=0.8, step=0.05)
quota_anticipo = 1.0 - quota_mutuo

st.sidebar.markdown(f"**Anticipo richiesto:** {quota_anticipo*100:.0f}%")

st.sidebar.header("Parametri tasso")
tasso_min = st.sidebar.number_input("Tasso minimo (%)", value=2.8, step=0.1)
tasso_max = st.sidebar.number_input("Tasso massimo (%)", value=3.3, step=0.1)
tasso_fisso = st.sidebar.number_input("Tasso fisso per analisi dettagliata (%)", value=3.0, step=0.1)

anticipo_max = st.sidebar.number_input("Anticipo massimo che possiamo mettere (€)", value=60000, step=5000)

rata_massima_sostenibile = stipendio * quota_rata

tab_budget, tab_casa = st.tabs(["💶 Quanto possiamo spendere", "🔨 Una casa precisa"])

# ==============================
# TAB 1 — BUDGET
# ==============================

with tab_budget:

    # 1) Plot mutuo & valore vs tasso
    st.subheader("1️⃣ Mutuo massimo e valore immobile vs tasso")

    st.markdown(
        "Questa sezione mostra, in funzione del tasso, quale sia il valore massimo di mutuo/immobile che possiamo permetterci."
    )

    fig1, tassi, mutui, immobili = fig_mutuo_vs_tasso(
        stipendio, anni, quota_mutuo, quota_rata, tasso_min, tasso_max
    )
    st.pyplot(fig1)

    # mutuo / casa al tasso fisso scelto
    mutuo_massimo_fisso = calcola_mutuo_massimo(stipendio, quota_rata, tasso_fisso, anni)
    valore_max_immobile_fisso = mutuo_massimo_fisso / quota_mutuo

    st.markdown(
        f"""
**Ad esempio, al tasso fisso del {tasso_fisso:.2f}%** possiamo ottenere indicativamente:
- Mutuo massimo (con rata = {quota_rata*100:.0f}% dello stipendio): **€ {mutuo_massimo_fisso:,.0f}**
- Valore massimo della casa (con mutuo {quota_mutuo*100:.0f}%): **€ {valore_max_immobile_fisso:,.0f}**
"""
    )

    # 2) Anticipo vs valore casa
    st.subheader("2️⃣ Anticipo vs valore immobile")
    st.markdown(
        "Questa sezione tiene conto di quale sia l'anticipo massimo che possiamo permetterci, ponendo un tetto più realistico al budget."
    )

    fig2 = fig_anticipo_vs_valore(
        valore_max_immobile_fisso,
        quota_anticipo,
        tasso_fisso,
        anni,
        anticipo_max
    )
    st.pyplot(fig2)

    valore_limite_anticipo = anticipo_max / quota_anticipo if quota_anticipo > 0 else float("inf")

    st.markdown(
        f"""
- Anticipo massimo che possiamo permetterci: **€ {anticipo_max:,.0f}**
- Questo corrisponde a un valore immobile di **€ {valore_limite_anticipo:,.0f}** (dato l'anticipo {quota_anticipo*100:.0f}%)
"""
    )

    # 3) Scenario 100% mutuo
    st.subheader("3️⃣ Scenario ipotetico: 100% mutuo (nessun anticipo)")

    mutuo_massimo_100 = calcola_mutuo_massimo(stipendio, quota_rata, tasso_fisso, anni)
    valore_max_immobile_100 = mutuo_massimo_100  # se il mutuo è 100%
    rata_100 = calcola_rata(mutuo_massimo_100, tasso_fisso, anni)

    st.markdown(
        f"""
Se una banca finanziasse il **100%** del valore della casa (vantaggi per under 36):

- Valore massimo immobile (100% mutuo, tasso al {tasso_fisso:.1f}%): **€ {valore_max_immobile_100:,.0f}**
- **Rata mensile** al {tasso_fisso:.1f}% per {anni} anni: **€ {rata_100:,.2f}**
"""
    )

    st.info("Hai una casa precisa in mente? Vai alla scheda **🔨 Una casa precisa** per sommare prezzo, costi di acquisto e lavori.")

# ==============================
# TAB 2 — UNA CASA PRECISA
# ==============================

with tab_casa:

    st.markdown(
        "Qui mettiamo **tutto** quello che costa una casa precisa: prezzo, costi di acquisto e ristrutturazione. "
        "Alla fine vediamo se mutuo e risparmi bastano. I parametri del mutuo sono quelli della barra laterale."
    )

    # 1) Prezzo e costi di acquisto
    st.subheader("1️⃣ Prezzo e costi di acquisto")

    prezzo_immobile = st.number_input("Prezzo dell'immobile (€)", min_value=50000.0, max_value=2000000.0,
                                      value=300000.0, step=10000.0)

    c1, c2 = st.columns(2)
    agenzia_pct = c1.number_input("Agenzia (% del prezzo, + IVA 22%)", min_value=0.0, max_value=6.0, value=3.0, step=0.5)
    notaio = c2.number_input("Notaio (€)", min_value=0, value=2500, step=250)
    imposte = c1.number_input(
        "Imposte di acquisto (€)", min_value=0, value=4000, step=250,
        help="Prima casa da privato: imposta di registro al 2% del valore catastale (non del prezzo) "
             "più 100 € di imposte fisse. Il notaio ti dà la cifra esatta."
    )
    altre_spese = c2.number_input(
        "Perizia, istruttoria mutuo, assicurazioni (€)", min_value=0, value=1500, step=250
    )
    costo_agenzia = prezzo_immobile * agenzia_pct / 100 * 1.22
    costi_acquisto = costo_agenzia + notaio + imposte + altre_spese
    st.markdown(f"Costi di acquisto: **€ {costi_acquisto:,.0f}** (di cui agenzia € {costo_agenzia:,.0f})")

    # 2) Ristrutturazione
    st.subheader("2️⃣ Ristrutturazione")

    modo_lavori = st.radio(
        "Come stimiamo i lavori?",
        ["Stima veloce a €/mq", "Computo dettagliato", "Nessun lavoro"],
        horizontal=True,
    )

    aliquota_detrazione = 0
    lavori_totale = 0.0

    if modo_lavori == "Stima veloce a €/mq":
        cq1, cq2 = st.columns(2)
        mq = cq1.number_input("Superficie (mq)", min_value=10, value=100, step=5)
        euro_mq = cq2.slider("Costo lavori tutto compreso (€/mq)", min_value=100, max_value=1500, value=700, step=25,
                             help="Indicativo: 300–500 €/mq rinfresco, 700–1.000 €/mq ristrutturazione completa con impianti.")
        lavori_totale = mq * euro_mq
        aliquota_detrazione = st.selectbox("Detrazione fiscale", [50, 36, 0], format_func=lambda x: f"{x}%" if x else "Nessuna",
                                           key="detr_veloce")
        st.markdown(f"Lavori stimati: **€ {lavori_totale:,.0f}**")

    elif modo_lavori == "Computo dettagliato":
        caricato = st.file_uploader(
            "Carica il computo (CSV con le colonne n, categoria, lavorazione, quantita, um, prezzo, codice, nota)",
            type="csv",
        )
        computo_base = None
        if caricato:
            try:
                computo_base = carica_computo(caricato)
            except Exception as err:
                st.error(f"Non riesco a leggere il CSV. {err}")
        else:
            st.info("Il computo non è salvato nell'app: caricalo qui sopra. "
                    "Puoi partire dal modello e riempirlo con le voci del preventivo.")
            st.download_button("Scarica il modello CSV", MODELLO_CSV.encode("utf-8"),
                               file_name="modello_computo.csv", mime="text/csv")

    if modo_lavori == "Computo dettagliato" and computo_base is not None:
        computo_mod = st.data_editor(
            computo_base,
            hide_index=True,
            num_rows="fixed",
            disabled=["n", "categoria", "lavorazione", "um", "codice", "nota"],
            column_order=["includi", "n", "lavorazione", "quantita", "um", "prezzo", "nota"],
            column_config={
                "includi": st.column_config.CheckboxColumn("✓", width="small"),
                "n": st.column_config.NumberColumn("N.", width="small"),
                "lavorazione": st.column_config.TextColumn("Lavorazione", width="medium"),
                "quantita": st.column_config.NumberColumn("Quantità", format="%.2f", min_value=0),
                "um": st.column_config.TextColumn("U.m.", width="small"),
                "prezzo": st.column_config.NumberColumn("Prezzo €", format="%.2f", min_value=0),
                "nota": st.column_config.TextColumn("Nota"),
            },
            key="editor_computo",
        )

        scenari = {}
        if scenari_applicabili(computo_mod):
            st.markdown("**Scenari da verificare col tecnico**")
            for chiave, testo in SCENARI.items():
                scenari[chiave] = st.checkbox(testo, key=f"scenario_{chiave}")
            if any(scenari.values()):
                st.caption("Gli scenari si applicano sopra la tabella e ricalcolano anche le macerie da portare in discarica.")
        computo_eff = applica_scenari(computo_mod, scenari)

        computo = totale_computo(computo_eff)
        originale = totale_computo(computo_base)

        ci1, ci2 = st.columns(2)
        iva_pct = ci1.selectbox("IVA sui lavori", [10, 22, 0], format_func=lambda x: f"{x}%",
                                help="Per i lavori su un'abitazione di solito è al 10%.")
        aliquota_detrazione = ci2.selectbox("Detrazione fiscale", [50, 36, 0],
                                            format_func=lambda x: f"{x}%" if x else "Nessuna",
                                            help="50% di norma per l'abitazione principale, 36% per le altre. "
                                                 "Tetto 96.000 €, in 10 rate annuali. Da verificare col commercialista.")
        iva = computo * iva_pct / 100

        with st.expander("Costi che il computo non copre (stime da regolare)", expanded=False):
            e1, e2 = st.columns(2)
            quantita = quantita_da_computo(computo_base)
            q1, q2, q3, q4, q5 = st.columns(5)
            extra = {
                "pavimenti_mq": q1.number_input("Pavimenti (mq)", min_value=0.0, value=quantita["pavimenti_mq"], step=1.0),
                "rivestimenti_mq": q2.number_input("Rivestim. (mq)", min_value=0.0, value=quantita["rivestimenti_mq"], step=1.0),
                "battiscopa_m": q3.number_input("Battiscopa (m)", min_value=0.0, value=quantita["battiscopa_m"], step=5.0),
                "n_porte": q4.number_input("Porte", min_value=0, value=quantita["n_porte"], step=1),
                "n_bagni": q5.number_input("Bagni", min_value=0, value=quantita["n_bagni"], step=1),
                "prezzo_pavimenti": e1.slider("Piastrelle pavimenti (€/mq)", 10, 80, 30),
                "prezzo_rivestimenti": e2.slider("Rivestimenti bagni (€/mq)", 15, 90, 35),
                "prezzo_battiscopa": e1.slider("Battiscopa (€/m)", 3, 20, 8),
                "prezzo_porta": e2.slider("Porte interne (€/porta)", 150, 900, 350, step=10),
                "porta_blindata": e1.slider("Porta blindata (€)", 800, 3000, 1500, step=50),
                "prezzo_bagno": e2.slider("Sanitari, rubinetti, doccia (€/bagno)", 800, 5000, 2000, step=100),
                "riscaldamento": e1.slider("Riscaldamento e clima (€)", 0, 35000, 12000, step=500,
                                           help="Assente dal computo."),
                "finestre_extra": e2.slider("Controtelai finestre, davanzali, soglie (€)", 0, 4000, 1500, step=100),
                "tecnici_pct": e1.slider("Tecnico, pratiche, sicurezza (% del computo)", 0.0, 12.0, 8.0, step=0.5),
                "imprevisti_pct": e2.slider("Imprevisti (% del computo)", 0, 20, 10),
            }
            st.caption("Le quantità sono lette dalle voci di sola posa del computo: controllale.")
        voci_extra = costi_extra(computo, extra)
        fuori_computo = sum(voci_extra.values())
        lavori_totale = computo + iva + fuori_computo

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Computo", f"€ {computo:,.0f}",
                  delta=f"{computo - originale:,.0f}" if abs(computo - originale) > 1 else None,
                  delta_color="inverse")
        m2.metric(f"IVA {iva_pct}%", f"€ {iva:,.0f}")
        m3.metric("Fuori computo", f"€ {fuori_computo:,.0f}")
        m4.metric("Totale lavori", f"€ {lavori_totale:,.0f}")

        per_categoria = totali_per_categoria(computo_eff)
        voci = {**per_categoria.to_dict(), **voci_extra}
        st.pyplot(fig_lavori_per_voce(voci, n_computo=len(per_categoria)))
        st.caption("In rosa le voci del computo, in grigio quelle che il computo non copre (IVA esclusa).")

        st.download_button(
            "Scarica il computo modificato (CSV)",
            computo_eff.drop(columns="includi")[computo_eff["includi"]].to_csv(index=False).encode("utf-8"),
            file_name="computo_modificato.csv",
            mime="text/csv",
        )

    # 3) Ce la facciamo?
    st.subheader("3️⃣ Ce la facciamo?")

    lavori_nel_mutuo = st.radio(
        "I lavori li paghiamo…",
        ["con i risparmi", "nel mutuo (acquisto + ristrutturazione)"],
        horizontal=True,
        disabled=lavori_totale == 0,
    ) != "con i risparmi"

    piano = piano_finanziario(prezzo_immobile, costi_acquisto, lavori_totale, quota_mutuo, lavori_nel_mutuo)
    rata = calcola_rata(piano["mutuo"], tasso_fisso, anni)
    detrazione_totale = detrazione(lavori_totale, aliquota_detrazione)
    detrazione_annua = detrazione_totale / 10
    mancano = max(0.0, piano["contanti"] - anticipo_max)
    risparmi_usati = min(piano["contanti"], anticipo_max)

    k1, k2, k3 = st.columns(3)
    k1.metric("Costo totale", f"€ {piano['totale']:,.0f}")
    k2.metric("Contanti necessari", f"€ {piano['contanti']:,.0f}",
              delta=f"{anticipo_max - piano['contanti']:,.0f} rispetto ai risparmi")
    k3.metric("Rata mensile", f"€ {rata:,.0f}",
              delta=f"{rata_massima_sostenibile - rata:,.0f} rispetto al massimo")

    st.pyplot(fig_copertura(prezzo_immobile, costi_acquisto, lavori_totale,
                            piano["mutuo"], risparmi_usati, mancano))

    st.pyplot(fig_rata_nel_tempo(rata, rata_massima_sostenibile, detrazione_annua, anni))

    st.markdown(
        f"""
- Mutuo richiesto ({quota_mutuo*100:.0f}% di {"prezzo + lavori" if lavori_nel_mutuo else "prezzo"}): **€ {piano['mutuo']:,.0f}**
- Contanti necessari (anticipo + costi di acquisto{"" if lavori_nel_mutuo else " + lavori"}): **€ {piano['contanti']:,.0f}**, risparmi disponibili **€ {anticipo_max:,.0f}**
- Rata a {tasso_fisso:.2f}% per {anni} anni: **€ {rata:,.2f}**, rata massima sostenibile **€ {rata_massima_sostenibile:,.2f}**
"""
        + (f"- Detrazione: **€ {detrazione_totale:,.0f}** in 10 anni, cioè circa **€ {detrazione_annua/12:,.0f} al mese** "
           f"che tornano con le tasse\n" if detrazione_totale else "")
    )

    problemi = []
    if mancano > 0:
        problemi.append(f"mancano **€ {mancano:,.0f}** di contanti")
    if rata > rata_massima_sostenibile:
        problemi.append(f"la rata supera il limite di **€ {rata - rata_massima_sostenibile:,.0f}** al mese")
    if not problemi:
        st.success("✅ Con questi numeri ce la facciamo: bastano i risparmi e la rata è entro il limite.")
    else:
        st.error("⚠️ Così non ci stiamo: " + " e ".join(problemi) + ".")

    if lavori_nel_mutuo:
        st.caption("Il mutuo acquisto + ristrutturazione di solito richiede il computo approvato dalla banca, "
                   "e i soldi dei lavori arrivano a stati di avanzamento. La banca finanzia in base alla sua perizia, "
                   "non al prezzo.")
