# Task 1.2 — Coral Garden Ridge Modelling

## Descrizione del task

Il task consiste nella **modellazione 3D del coral garden** presente nel Flume Tank (in corrente) durante il World Championship. Il coral garden è una struttura in pipe PVC da ½ pollice con le seguenti caratteristiche (regolamento 2026 EXPLORER, Task 1.2):

- Lunghezza: tra 1 m e 2,5 m
- Larghezza: circa 36 cm
- Altezza: non nota a priori (include eventuali tee PVC in cima; si misura dal fondo della struttura alla sua sommità)
- **8 target** (quadrati 10 × 10 cm in plastica corrugata colorata) applicati sul PVC, distribuiti sul lato frontale e su quello posteriore

---

## Approccio scelto: Computer Vision su due foto (fronte + retro)

L'approccio implementato è la **misurazione automatica tramite visione artificiale** (OpenCV) a partire da **due fotografie** acquisite dal ROV — una frontale e una posteriore. Una sola foto non vede tutti gli 8 target (alcuni sono sul lato frontale, altri sul retro): le due viste insieme li coprono tutti.

Il processo prevede:

1. Il ROV posiziona un **righello verde da 50 cm** accanto alla struttura come riferimento metrico.
2. Il ROV acquisisce una **foto frontale** del coral garden. Il righello verde deve essere visibile nell'inquadratura.
3. Il ROV (o l'operatore) **sposta il righello verde** sul lato opposto e acquisisce una **foto posteriore** — anche qui col righello visibile. Ogni foto ha quindi la propria scala pixel/cm indipendente.
4. Lo script `final.py` analizza entrambe le immagini e:
   - rileva il righello verde in ciascuna per calcolare la scala pixel/cm
   - rileva e conta i target colorati (qualsiasi colore eccetto blu dell'acqua) e **somma le due viste** (limite 8)
   - isola i tubi PVC bianchi e ne misura lunghezza e altezza reale (prende il **max** delle due viste)
5. Le misure aggregate vengono scritte automaticamente in `equations.txt`.
6. SolidWorks legge `equations.txt` come file equazioni e scala il modello CAD (`Coral garden (CAD).SLDPRT`) in automatico. **Sul modello vanno posizionati tutti e 8 i target colorati** (≈ quelli visti nelle due foto) così il modello ruotabile li mostra tutti → criterio "8 target = 20 pt".

> **Nota sul righello**: l'oggetto conta come debris se non viene rimosso o controllato dal ROV entro la fine del product demonstration time.

> **Nota onesta sul metodo e i punti**: misurare con la CV e inserire le quote in un modello SolidWorks parametrico è, per il regolamento, il **metodo CAD manuale** (max 30 pt); due foto fronte/retro non sono fotogrammetria multi-view classica. Modellare tutti e 8 i target rafforza comunque la richiesta del criterio "8 target" e massimizza i punti rivendicabili. I giudici assegnano i punti **per un solo metodo**.

---

## Pipeline

```
Foto FRONTE + righello verde 50 cm     Foto RETRO + righello verde 50 cm
           │                                      │
           ▼                                      ▼
      analyze() (OpenCV)                     analyze() (OpenCV)
   scala · target · misure PVC           scala · target · misure PVC
           │                                      │
           └──────────────┬───────────────────────┘
                          ▼
                  analyze_pair() — aggregazione
        target = somma (cap 8) · lunghezza/altezza = max
                          │
                          ▼
                     equations.txt
                     "lunghezza" = X
                     "altezza"   = Y
                          │
                          ▼
              SolidWorks (equazioni)
              Coral garden (CAD).SLDPRT
              → modello scalato + 8 target posizionati
```

---

## Script

| File | Ruolo |
|---|---|
| `rilevatore_target.py` | Prototipo iniziale: rileva solo target rosa/magenta |
| `target.py` | Versione intermedia: scala + misura tubi PVC bianchi (righello verde) |
| `final.py` | **Script finale**: pipeline completa per coppia fronte/retro (scala → target universali → misure PVC → aggregazione → export equazioni CAD) |
| `genera_test_verde.py` | Utility: genera immagini di test sintetiche con righello verde da `righello.jpg` |

### Dettaglio `final.py`

La funzione `analyze(image_path, ...)` elabora **una** immagine; `analyze_pair(fronte, retro, ...)` la richiama su entrambe le foto e aggrega i risultati.

**Fase 1 — Scala pixel/cm**
Rileva il righello verde (HSV `[35,70,50]`→`[85,255,255]`) tramite `findContours`, calcola `pixels_per_cm = lunghezza_righello_px / 50`.

**Fase 2 — Rilevamento target**
Maschera HSV su colori saturi escludendo sia il blu dell'acqua (`[85,40,40]`→`[135,255,255]`) sia il **bianco/grigio** (bassa saturazione, alto valore: `[0,0,150]`→`[180,60,255]`), così i tubi PVC e i **quadrati bianchi vengono ignorati** e contano solo i quadrati colorati. Filtra le forme con 4–6 lati (quadrati in prospettiva). L'area del righello viene esclusa per evitare falsi positivi.

**Fase 3 — Misura struttura PVC**
Isola i tubi bianchi (bassa saturazione, alto valore: `[0,0,180]`→`[180,50,255]`), calcola il bounding box di tutti i pixel PVC e converte larghezza e altezza in cm reali.

**Aggregazione (`analyze_pair`)**
Somma i target delle due viste (limitati a 8) e prende il `max` di lunghezza e altezza tra fronte e retro. Scrive `equations.txt` **una sola volta** con le quote aggregate.

**Fase 4 — Export CAD**
Scrive `equations.txt` con i valori `"lunghezza"` e `"altezza"` nel formato che SolidWorks usa come variabili globali.

---

## Utilizzo

```bash
pip install opencv-python numpy
python final.py
```

Lo script è configurato per leggere `fronte.jpg` e `retro.jpg`. Sostituisci questi due file con le tue foto reali (vista frontale e posteriore, righello verde visibile in ciascuna) e rilancia `python final.py`.

Per provare la pipeline senza foto reali, genera prima immagini di test sintetiche con righello verde:

```bash
python genera_test_verde.py   # crea fronte.jpg e retro.jpg da righello.jpg
python final.py
```

Per cambiare i nomi delle due foto, modificare l'ultima riga di `final.py`:

```python
analyze_pair('fronte.jpg', 'retro.jpg')
```

---

## Criteri di punteggio

### Metodo fotogrammetrico / CV (max 40 pt)

| Risultato | Punti |
|---|---|
| Modello 3D visualizzato, nessun target visibile | 5 pt |
| 1–3 target visibili sul modello | 10 pt |
| 4–7 target visibili sul modello | 15 pt |
| Tutti e 8 i target visibili sul modello | **20 pt** |
| Lunghezza misurata entro ±5 cm dalla reale | **+10 pt** |
| Modello scalato con lunghezza vera visualizzata | **+5 pt** |
| Altezza stimata entro ±5 cm (dal modello scalato) | **+5 pt** |

### Metodo manuale CAD (max 30 pt, alternativo)

| Risultato | Punti |
|---|---|
| Lunghezza misurata entro ±5 cm | 10 pt |
| Altezza misurata entro ±5 cm | 10 pt |
| Modello CAD 3D con misure incluse | 10 pt |

> **Nota**: i punti vengono assegnati **solo per un metodo**. Se la CV ha successo si ottengono fino a 40 pt; se fallisce, il modello CAD manuale garantisce fino a 30 pt.

---

## Requisiti per il product demonstration

- Il modello 3D (`Coral garden (CAD).SLDPRT`) deve essere **visualizzato su schermo** alla mission station.
- Deve essere **ruotabile** per consentire al giudice di vederlo da qualsiasi angolazione.
- I **target colorati** devono essere visibili sul modello.
- Le **misure di lunghezza e altezza** devono essere incluse.

---

## Note operative

- Richiedere la **lunghezza vera** al giudice subito dopo aver fornito la propria misurazione.
- Verificare prima della demo che SolidWorks abbia caricato i valori aggiornati da `equations.txt`.
- I range HSV sono tarati per condizioni di luce normale — in acqua torbida potrebbero essere necessari aggiustamenti.

---

## Struttura della cartella

```
Task 1.2/
├── README.md
├── final.py                      ← script principale (usare questo)
├── genera_test_verde.py          ← genera fronte.jpg/retro.jpg di test (righello verde)
├── target.py                     ← versione precedente (solo PVC)
├── rilevatore_target.py          ← prototipo iniziale (solo rosa)
├── equations.txt                 ← output misure → input SolidWorks
├── Coral garden (CAD).SLDPRT    ← modello SolidWorks con equazioni
├── fronte.jpg / retro.jpg        ← coppia di foto analizzate (test o reali)
├── righello.jpg                  ← immagine sorgente (righello originale)
├── nuova.jpg                     ← immagine di test aggiuntiva
├── Coral garden.zip              ← archivio progetto
└── colar_garden.zip              ← archivio progetto (versione precedente)
```
