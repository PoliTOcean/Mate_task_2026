# Task 1.2 — Coral Garden Ridge Modelling

## Descrizione del task

Il task consiste nella **modellazione 3D del coral garden** presente nel Flume Tank durante il World Championship. Il coral garden è una struttura in pipe PVC da ½ pollice con le seguenti caratteristiche:

- Lunghezza: tra 1 m e 2,5 m
- Larghezza: circa 36 cm
- Altezza: non nota a priori
- **8 target** (quadrati 10 × 10 cm in plastica corrugata colorata) applicati sul PVC

---

## Approccio scelto: ricostruzione 3D da fronte + retro (Computer Vision)

I **8 target** sono distribuiti **su entrambi i lati** della struttura: per averli tutti sul modello servono **due foto**, una del **fronte** e una del **retro**. L'approccio implementato analizza entrambe le viste con OpenCV e **genera direttamente il modello 3D** (ruotabile a schermo + esportabile in `.obj`), senza dipendere dal CAD.

Il flusso è **ibrido**: oltre al modello 3D generato, lo script continua a scrivere `equations.txt`, così SolidWorks resta disponibile come **fallback**.

Il processo prevede:

1. Il ROV posiziona un **righello arancione da 50 cm** accanto alla struttura come riferimento metrico (sul lato fronte).
2. Il ROV acquisisce **due fotografie**: il **fronte** (con righello arancione) e il **retro**.
3. Lo script `final.py`:
   - rileva il righello arancione sul fronte → scala pixel/cm;
   - su ciascun lato rileva i target colorati (qualsiasi colore eccetto blu dell'acqua) e ne ricava **posizione in cm** e **colore reale**;
   - isola i tubi PVC bianchi e misura **lunghezza** e **altezza** reali;
   - riusa la scala del fronte per il **retro** (il cui righello è trasparente, non rilevabile col filtro arancione).
4. `model_3d.py` + `frame.py` costruiscono il **telaio a macroblocchi**: la struttura (topologia nota dal manuale) è composta da pochi parallelepipedi 3D uniti — **ala sinistra** (box basso) + **torre centrale** (box alto) + **ala destra** (box medio) + **base** — scalati a (L, H, profondità) misurati dalle foto. Sempre intero e connesso. I target rilevati vengono **agganciati al tubo più vicino** (fronte `z=0`, retro `z=36`).
5. Output: **viewer 3D ruotabile** (matplotlib) per la demo, file **`coral_garden.obj`** per portabilità, ed **`equations.txt`** come fallback SolidWorks.

> **Profondità**: la larghezza della struttura (~36 cm, nota da regolamento) è usata come profondità fissa. Con due sole foto non calibrate non si stima per parallasse.

> **Nota sul righello**: l'oggetto conta come debris se non viene rimosso o controllato dal ROV entro la fine del product demonstration time.

---

## Pipeline

```
Foto FRONTE (+righello 50 cm)      Foto RETRO (righello trasparente)
        │                                   │
        ▼                                   ▼
   analyze() ──scala pixel/cm──────────► analyze() (riusa la scala)
        │                                   │
        │ length, height,                   │ pvc_mask,
        │ pvc_mask, targets[]               │ targets[]
        │ (x,y in cm + colore)              │ (x,y in cm + colore)
        └──────────────┬────────────────────┘
                       ▼
            model_3d.build_model() + frame.py
            macroblocchi (ala sx + torre +
            ala dx + base) scalati + target
                       │
        ┌──────────────┼───────────────────┐
        ▼              ▼                    ▼
  viewer 3D       coral_garden.obj    equations.txt
  ruotabile       (export portabile)  (fallback SolidWorks)
  (demo)
```

---

## Script

| File | Ruolo |
|---|---|
| `rilevatore_target.py` | Prototipo iniziale: rileva solo target rosa/magenta |
| `target.py` | Versione intermedia: scala + misura tubi PVC bianchi |
| `final.py` | **Script principale**: analisi CV per lato (`analyze`) + orchestratore fronte/retro (`ricostruisci_3d`) |
| `model_3d.py` | **Ricostruzione 3D**: `build_model` (fonde i due lati → telaio a macroblocchi), `show_interactive` (viewer ruotabile), `export_mesh` (`.obj`) |
| `frame.py` | **Telaio**: `build_frame` (macroblocchi ala sx + torre + ala dx + base), `snap_target_to_frame` (aggancia i target al tubo più vicino) |

### Dettaglio `final.py` — `analyze(image_path, ..., pixels_per_cm=None, write_equations=True)`

**Fase 1 — Scala pixel/cm**
Rileva il righello arancione (HSV `[5,150,150]`→`[25,255,255]`) tramite `findContours`, calcola `pixels_per_cm = lunghezza_righello_px / 50`. Se si passa `pixels_per_cm` (lato retro col righello trasparente), questa fase viene **saltata** e si riusa la scala fornita.

**Fase 2 — Rilevamento target (posizione + colore)**
Maschera HSV su colori **vividi** (saturazione ≥ 90, qualunque tinta) escludendo il blu dell'acqua (`[85,40,40]`→`[135,255,255]`): fondali/detriti/legno/ombre desaturati cadono, i target colorati restano. Filtra le forme con 4–6 lati e applica un **filtro dimensione basato sulla scala** (i target sono ~10×10 cm: si scartano forme troppo piccole/grandi o poco quadrate — corde, riflessi, oggetti dell'ambiente). Per ogni target salva **centro in cm** (rispetto allo spigolo in basso a sinistra del box PVC) e **colore medio reale** (per il 3D). L'area del righello viene esclusa per evitare falsi positivi.

**Fase 3 — Misura struttura PVC + maschera per la validazione**
Isola i tubi bianchi (bassa saturazione, alto valore: `[0,0,180]`→`[180,50,255]`), calcola il bounding box di tutti i pixel PVC (→ lunghezza/altezza in cm) ed espone la **maschera PVC** + bbox. È questa maschera che, in `frame.py`, valida quali tubi della griglia candidata esistono davvero (sono coperti da bianco) → telaio fedele e connesso.

**Export** — `equations.txt` (fallback SolidWorks, solo se `write_equations=True`) + `coral_garden.obj` (via `model_3d.export_mesh`).

### `ricostruisci_3d(front_path, back_path, depth_cm=36)`

Orchestratore: analizza fronte → analizza retro riusando la scala → `build_model` → scrive `equations.txt` ed esporta `.obj` → apre il viewer 3D.

---

## Utilizzo

```bash
pip install opencv-python numpy matplotlib
python final.py                       # usa righello.jpg (fronte) + nuova.jpg (retro)
python final.py --front fronte.jpg --back retro.jpg --depth 36
python final.py --back ""             # solo vista frontale
python final.py --no-show             # senza viewer (utile per i test)
```

Il viewer 3D è **ruotabile col mouse**: pronto da proiettare alla mission station. `coral_garden.obj` è apribile in qualsiasi viewer 3D esterno (3D Viewer, MeshLab, Blender).

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
├── final.py                      ← script principale (analyze + ricostruisci_3d)
├── model_3d.py                   ← ricostruzione 3D (viewer + export .obj)
├── frame.py                      ← telaio di tubi (griglia validata sui pixel)
├── target.py                     ← versione precedente (solo PVC)
├── rilevatore_target.py          ← prototipo iniziale (solo rosa)
├── equations.txt                 ← output misure → fallback SolidWorks
├── coral_garden.obj              ← modello 3D esportato (generato)
├── Coral garden (CAD).SLDPRT    ← modello SolidWorks (fallback)
├── righello.jpg                  ← immagine di test (fronte)
├── nuova.jpg                     ← immagine di test (retro)
├── Coral garden.zip              ← archivio progetto
└── colar_garden.zip              ← archivio progetto (versione precedente)
```
