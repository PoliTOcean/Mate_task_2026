# Task 2.2 — Iceberg Threat Level

## Descrizione del task

Dato un iceberg rilevato in superficie (posizione, rotta e profondità della chiglia), il task richiede di valutare il **livello di minaccia** — verde / giallo / rosso — verso le **4 piattaforme petrolifere** dei Grand Banks, sia per la **piattaforma di superficie** sia per gli **asset subsea** (pipeline, manifold, wellhead sul fondale).

| Componente | Punti |
|---|---|
| Minaccia alle 4 piattaforme di superficie | 10 pt |
| Minaccia agli asset subsea | 5 pt |
| **Totale massimo** | **15 pt** |

> La survey dei dati dell'iceberg e la **misura della keel depth** restano operazioni ROV / manuali: questo modulo riceve la keel depth come input e svolge solo il **calcolo puro** (niente computer vision, niente modello).

---

## Piattaforme (costanti da regolamento)

Coordinate e profondità dell'oceano sono **fisse** (non sono input). Nel manuale le profondità sono negative; qui memorizzate come positive.

| Platform   | Lat      | Lon       | Ocean depth (m) |
|------------|----------|-----------|-----------------|
| Hibernia   | 43.7504  | -48.7819  | 78  |
| Sea Rose   | 46.7895  | -48.1417  | 107 |
| Terra Nova | 46.4     | -48.4     | 91  |
| Hebron     | 46.544   | -48.498   | 93  |

---

## Approccio: Closest Point of Approach (CPA)

L'iceberg si muove in linea retta lungo l'heading (bearing bussola: 0°=Nord, 90°=Est, orario). Per ogni piattaforma si calcola la **distanza di passaggio** (closest approach distance) tra la piattaforma e la traiettoria dell'iceberg.

### Geometria

Proiezione planare locale (equirettangolare) centrata sull'iceberg, con la regola **1 minuto di latitudine = 1 NM**:

```
x_EST  = (lon_platform - lon_iceberg) * 60 * cos(lat_iceberg)   # NM verso Est
y_NORD = (lat_platform - lat_iceberg) * 60                       # NM verso Nord
```

L'iceberg è nell'origine `(0,0)` e si muove lungo il versore direzione `d = (sin θ, cos θ)`. Poiché `d` è unitario, la distanza perpendicolare dalla piattaforma `P=(x,y)` alla retta di moto è il prodotto vettoriale 2D:

```
passing_distance_nm = abs(x * d_y - y * d_x)
```

> **Da validare prima della gara:** questa interpretazione usa la **retta infinita** (CPA indipendente dal verso di marcia). Va verificata contro gli **Iceberg track practice examples** nella sezione *Product Demonstration Resources* del sito MATE. Se i practice example mostrassero che conta solo la **semiretta in avanti**, abilitare il flag `forward_only=True`: se la piattaforma cade "dietro" l'iceberg (prodotto scalare `x*d_x + y*d_y < 0`) si usa la distanza corrente `sqrt(x²+y²)` invece della perpendicolare.

---

## Regole di classificazione

Sia `keel_ratio = keel_depth_m / water_depth_m` (entrambe positive).

### Minaccia alla piattaforma di SUPERFICIE (nell'ordine)

1. `keel_ratio >= 1.10` → **green** — regola del 110%: l'iceberg si arena prima di arrivare
2. `passing_distance < 5 NM` → **red**
3. `5 <= passing_distance <= 10 NM` → **yellow**
4. `> 10 NM` → **green**

### Minaccia agli asset SUBSEA (nell'ordine)

1. `passing_distance > 25 NM` → **green** — fuori dai 25 NM, nessuna minaccia
2. `keel_ratio >= 1.10` → **green** — si arena prima
3. `0.90 <= keel_ratio < 1.10` → **red** — pericolo critico
4. `0.70 <= keel_ratio < 0.90` → **yellow** — può impattare il fondale
5. `keel_ratio < 0.70` → **green**

> **Scoring:** Subsea senza punti parziali (tutte e 4 corrette = 5 pt, altrimenti 0). Piattaforme: 4/4 = 10 pt, 3/4 = 5 pt, ≤2 = 0 pt.

---

## Struttura della cartella

```
Task 2.2/
├── README.md          ← questo file
├── iceberg.py         ← logica pura: evaluate() + demo CLI
└── test_iceberg.py    ← test con i golden value (CPA, classificazione)
```

---

## Utilizzo

```bash
python iceberg.py        # esegue la demo CLI (iceberg verso Terra Nova)
python test_iceberg.py   # esegue i test (o: pytest)
```

### API

```python
from iceberg import evaluate

res = evaluate(ice_lat=46.4, ice_lon=-48.5, heading_deg=90.0, keel_depth_m=95.0)
# res["platforms"] -> [{name, passing_distance_nm, water_depth_m,
#                       keel_ratio, surface_threat, subsea_threat}, ...]
```

`evaluate()` è pura e senza side-effect: è la stessa funzione che NEXUS wrappa nella route `/iceberg/evaluate`.

---

## Esempio di output

```
Platform      CPA (NM)   ratio   surface subsea
------------------------------------------------------
Hibernia        158.98   1.218   green   green
Sea Rose         23.37   0.888   green   yellow
Terra Nova         0.0   1.044   red     red
Hebron            8.64   1.022   yellow  red
```
