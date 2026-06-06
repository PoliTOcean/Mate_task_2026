# Task 1.2 — Coral Garden Ridge Modelling

## Descrizione del task

Il task consiste nella **modellazione 3D del coral garden** presente nel Flume Tank durante il World Championship. Il coral garden è una struttura in pipe PVC da ½ pollice con le seguenti caratteristiche:

- Lunghezza: tra 1 m e 2,5 m
- Larghezza: circa 36 cm
- Altezza: non nota a priori
- **8 target** (quadrati 10 × 10 cm in plastica corrugata colorata) applicati sul PVC

---

## Approccio scelto: Computer Vision su singola immagine

L'approccio implementato è la **misurazione automatica tramite visione artificiale** (OpenCV) su una singola immagine acquisita dal ROV. Non si utilizza software di fotogrammetria esterno.

Il processo prevede:

1. Il ROV posiziona un **righello arancione da 50 cm** accanto alla struttura come riferimento metrico.
2. Il ROV acquisisce **una fotografia** del coral garden dall'alto o di lato.
3. Lo script `final.py` analizza l'immagine e:
   - rileva il righello arancione per calcolare la scala pixel/cm
   - rileva e conta i target colorati (qualsiasi colore eccetto blu dell'acqua)
   - isola i tubi PVC bianchi e ne misura lunghezza e altezza reale
4. Le misure vengono scritte automaticamente in `equations.txt`.
5. SolidWorks legge `equations.txt` come file equazioni e scala il modello CAD (`Coral garden (CAD).SLDPRT`) in automatico.

> **Nota sul righello**: l'oggetto conta come debris se non viene rimosso o controllato dal ROV entro la fine del product demonstration time.

---

## Pipeline

```
Immagine ROV + righello arancione 50 cm
           │
           ▼
      final.py (OpenCV)
           │
     ┌─────┼─────────────────────┐
     ▼     ▼                     ▼
Scala   Rilevamento         Misura struttura
pixel   target colorati     PVC (bounding box)
/cm     (non-blu, forma     → lunghezza, altezza
        quadrata 4-6 lati)
           │
           ▼
      equations.txt
      "lunghezza" = X
      "altezza"   = Y
           │
           ▼
   SolidWorks (equazioni)
   Coral garden (CAD).SLDPRT
   → modello scalato automaticamente
```

---

## Script

| File | Ruolo |
|---|---|
| `rilevatore_target.py` | Prototipo iniziale: rileva solo target rosa/magenta |
| `target.py` | Versione intermedia: scala + misura tubi PVC bianchi |
| `final.py` | **Script finale**: pipeline completa (scala → target universali → misure PVC → export equazioni CAD) |

### Dettaglio `final.py`

**Fase 1 — Scala pixel/cm**
Rileva il righello arancione (HSV `[5,150,150]`→`[25,255,255]`) tramite `findContours`, calcola `pixels_per_cm = lunghezza_righello_px / 50`.

**Fase 2 — Rilevamento target**
Maschera HSV su colori saturi escludendo il blu dell'acqua (`[85,40,40]`→`[135,255,255]`). Filtra le forme con 4–6 lati (quadrati in prospettiva). L'area del righello viene esclusa per evitare falsi positivi.

**Fase 3 — Misura struttura PVC**
Isola i tubi bianchi (bassa saturazione, alto valore: `[0,0,180]`→`[180,50,255]`), calcola il bounding box di tutti i pixel PVC e converte larghezza e altezza in cm reali.

**Fase 4 — Export CAD**
Scrive `equations.txt` con i valori `"lunghezza"` e `"altezza"` nel formato che SolidWorks usa come variabili globali.

---

## Utilizzo

```bash
pip install opencv-python numpy
python final.py
```

Lo script è configurato per leggere `righello.jpg`. Per usare un'altra immagine, modificare l'ultima riga di `final.py`:

```python
analizza_coral_garden_universale('nome_immagine.jpg')
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
├── target.py                     ← versione precedente (solo PVC)
├── rilevatore_target.py          ← prototipo iniziale (solo rosa)
├── equations.txt                 ← output misure → input SolidWorks
├── Coral garden (CAD).SLDPRT    ← modello SolidWorks con equazioni
├── righello.jpg                  ← immagine di test
├── nuova.jpg                     ← immagine di test aggiuntiva
├── Coral garden.zip              ← archivio progetto
└── colar_garden.zip              ← archivio progetto (versione precedente)
```
