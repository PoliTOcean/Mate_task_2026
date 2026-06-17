# Task 2.5 — eDNA Frequency Calculator

## Descrizione del task

Dopo il recupero del sensore eDNA, il giudice fornisce i **conteggi delle 10 specie** rilevate. Il task richiede di calcolare e mostrare a schermo la **% di frequenza vista** di ciascuna specie:

```
frequenza_% = count_specie / totale * 100
```

È **calcolo puro** (aritmetica): niente computer vision, niente modello.

| Componente | Punti |
|---|---|
| Calcolo e visualizzazione della % per le 10 specie | **10 pt** |

---

## Approccio

La funzione `frequency()` accetta i conteggi come `dict {nome: count}` oppure come `list[{"name": ..., "count": ...}]`, somma il totale e calcola la percentuale di ogni specie. Restituisce sia la `percent` a **precisione piena** (per i confronti / i test) sia `percent_display` arrotondata a **2 decimali** (per la GUI e il giudice). Se il totale è ≤ 0 ritorna un errore strutturato.

---

## Golden test (dal manuale)

Conteggi di esempio (totale atteso **84**):

| Specie | Count | % |
|---|---|---|
| Snow crab | 19 | 22.62 |
| Acadian hermit crab | 3 | 3.57 |
| Western Atlantic Hairy Hermit Crab | 1 | 1.19 |
| European Green Crab | 9 | 10.71 |
| Rock Crab | 10 | 11.90 |
| Jonah Crab | 5 | 5.95 |
| Spiny Sunstar | 8 | 9.52 |
| Sea Urchin | 10 | 11.90 |
| Boreal Sea Star | 12 | 14.29 |
| Daisy brittle star | 7 | 8.33 |
| **TOTALE** | **84** | **100.00** |

I test verificano: `total == 84`, `Snow crab ≈ 22.619047619 %`, `Rock Crab ≈ 11.904761905 %`, somma delle percentuali `== 100.0`, esattamente 10 specie.

---

## Struttura della cartella

```
Task 2.5/
├── README.md       ← questo file
├── edna.py         ← logica pura: frequency() + demo CLI
└── test_edna.py    ← golden test (totale 84, % note)
```

---

## Utilizzo

```bash
python edna.py        # esegue la demo CLI con il sample del manuale
python test_edna.py   # esegue i test (o: pytest)
```

### API

```python
from edna import frequency

res = frequency({"Snow crab": 19, "Rock Crab": 10, ...})
# res -> {ok, total, species: [{name, count, percent, percent_display}, ...]}
```

`frequency()` è pura e senza side-effect: è la stessa funzione che NEXUS wrappa nella route `/edna/frequency`.

---

## Esempio di output

```
Species                                count        %
-----------------------------------------------------
Snow crab                                 19   22.62%
...
-----------------------------------------------------
TOTALE                                    84  100.00%
```
