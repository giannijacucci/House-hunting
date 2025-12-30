import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib
from matplotlib.ticker import MaxNLocator
import streamlit as st

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


# ==============================
# FUNZIONI DI CALCOLO
# ==============================

def calcola_mutuo_massimo(stipendio, quota_rata, tasso_annuo, anni):
    rata_max = stipendio * quota_rata
    tasso_mensile = (tasso_annuo / 100) / 12
    n_rate = anni * 12
    mutuo_massimo = rata_max * (1 - (1 + tasso_mensile) ** -n_rate) / tasso_mensile
    return mutuo_massimo


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

    for spine in ax.spines.values():
        spine.set_linewidth(axis_width)
    ax.tick_params(width=axis_width)

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

    for spine in ax.spines.values():
        spine.set_linewidth(axis_width)
    ax.tick_params(width=axis_width)

    fig.tight_layout()
    return fig


# ==============================
# APP STREAMLIT
# ==============================

st.set_page_config(page_title="Mutuo & Casa", page_icon="🏠", layout="centered")

st.title("🏠 Analizzatore di mutuo & valore immobile")

st.markdown(
    "Strumentino per capire **quanto puoi permetterti** in base allo stipendio, "
    "al tasso e all'anticipo."
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

anticipo_max = st.sidebar.number_input("Anticipo massimo che puoi mettere (€)", value=60000, step=5000)

# ==============================
# 1) Plot mutuo & valore vs tasso
# ==============================

st.subheader("1️⃣ Mutuo massimo e valore immobile vs tasso")

fig1, tassi, mutui, immobili = fig_mutuo_vs_tasso(
    stipendio, anni, quota_mutuo, quota_rata, tasso_min, tasso_max
)
st.pyplot(fig1)

# mutuo / casa al tasso fisso scelto
mutuo_massimo_fisso = calcola_mutuo_massimo(stipendio, quota_rata, tasso_fisso, anni)
valore_max_immobile_fisso = mutuo_massimo_fisso / quota_mutuo

st.markdown(
    f"""
**Al tasso fisso del {tasso_fisso:.2f}%** puoi ottenere indicativamente:
- Mutuo massimo (con rata = {quota_rata*100:.0f}% dello stipendio): **€ {mutuo_massimo_fisso:,.0f}**
- Valore massimo della casa (con mutuo {quota_mutuo*100:.0f}%): **€ {valore_max_immobile_fisso:,.0f}**
"""
)

# ==============================
# 2) Anticipo vs valore casa
# ==============================

st.subheader("2️⃣ Anticipo vs valore immobile")

fig2 = fig_anticipo_vs_valore(
    valore_max_immobile_fisso,
    quota_anticipo,
    tasso_fisso,
    anni,
    anticipo_max
)
st.pyplot(fig2)

valore_limite_anticipo = anticipo_max / quota_anticipo

st.markdown(
    f"""
- Anticipo massimo che vuoi/pensi di poter mettere: **€ {anticipo_max:,.0f}**
- Questo corrisponde a un valore immobile di **€ {valore_limite_anticipo:,.0f}** (dato l'anticipo {quota_anticipo*100:.0f}%)
"""
)

# ==============================
# 3) Scenario 100% mutuo
# ==============================

st.subheader("3️⃣ Scenario ipotetico: 100% mutuo (nessun anticipo)")

mutuo_massimo_100 = calcola_mutuo_massimo(stipendio, quota_rata, tasso_fisso, anni)
valore_max_immobile_100 = mutuo_massimo_100  # se il mutuo è 100%

st.markdown(
    f"""
Se (ipotesi) una banca ti finanziasse il **100%** del valore della casa:

- Mutuo massimo: **€ {mutuo_massimo_100:,.0f}**
- Valore massimo immobile (100% mutuo): **€ {valore_max_immobile_100:,.0f}**
"""
)

# ==============================
# 4) Prezzo specifico dell'immobile
# ==============================

st.subheader("4️⃣ Verifica un prezzo specifico")

prezzo_immobile = st.number_input("Prezzo dell'immobile da valutare (€)", min_value=50000.0, max_value=2000000.0, value=300000.0, step=10000.0)

if prezzo_immobile:
    anticipo_necessario = quota_anticipo * prezzo_immobile
    mutuo_richiesto = quota_mutuo * prezzo_immobile

    tasso_mensile = (tasso_fisso / 100) / 12
    n_rate = anni * 12
    rata_immobile = mutuo_richiesto * tasso_mensile / (1 - (1 + tasso_mensile) ** -n_rate)

    rata_massima_sostenibile = stipendio * quota_rata

    st.markdown(
        f"""
**Risultati per prezzo immobile = € {prezzo_immobile:,.0f}**

- Anticipo richiesto ({quota_anticipo*100:.0f}%): **€ {anticipo_necessario:,.0f}**
- Mutuo richiesto ({quota_mutuo*100:.0f}%): **€ {mutuo_richiesto:,.0f}**
- Rata mensile a {tasso_fisso:.2f}% per {anni} anni: **€ {rata_immobile:,.2f}**
- Rata massima sostenibile (quota_rata × stipendio): **€ {rata_massima_sostenibile:,.2f}**
"""
    )

    if rata_immobile <= rata_massima_sostenibile:
        st.success("✅ La rata è entro il limite di sostenibilità.")
    else:
        st.error("⚠️ La rata supera il limite di sostenibilità.")