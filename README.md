# 🏠 Case a prima vista

App Streamlit per capire quale casa possiamo permetterci: https://caseaprimavista.streamlit.app/

Due schede:

- **💶 Quanto possiamo spendere**: mutuo massimo in funzione di stipendio, tasso e anticipo.
- **🔨 Una casa precisa**: prezzo + costi di acquisto + ristrutturazione, e verifica se mutuo e risparmi bastano.

## File

| File | Cosa contiene |
|---|---|
| `app.py` | L'interfaccia e i grafici |
| `calcoli.py` | Le formule (rata, mutuo massimo, computo, piano finanziario) |
| `requirements.txt` | Le librerie che Streamlit Cloud installa |

## Come si aggiorna il sito

L'app su streamlit.app è collegata a questo repository su GitHub. **Ogni commit sul branch `main` aggiorna il sito da solo** in un paio di minuti. Non c'è altro da fare.

Due modi per modificarla:

1. **Dal browser**: su GitHub apri un file, clicca la matita ✏️, modifica e fai "Commit changes".
2. **Dal Mac**, per provarla prima di pubblicarla:

   ```bash
   git clone https://github.com/giannijacucci/House-hunting.git
   cd House-hunting
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/streamlit run app.py
   ```

   Si apre su http://localhost:8501. Quando va bene:

   ```bash
   git add -A
   git commit -m "Descrizione della modifica"
   git push
   ```

Se il sito mostra un errore, i log sono su https://share.streamlit.io (accedi con GitHub, apri l'app, "Manage app").

## Il computo dei lavori

Il computo **non è salvato nel repository** (che è pubblico): nella scheda "Una casa precisa" si carica ogni volta un CSV con le colonne
`n, categoria, lavorazione, quantita, um, prezzo, codice, nota`. Dall'app si può scaricare un modello vuoto.

La cartella `dati/` è esclusa da git (`.gitignore`): ci si possono tenere i CSV in locale senza rischio di pubblicarli.
