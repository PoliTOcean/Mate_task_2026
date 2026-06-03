# Task 1.2 — Coral Garden Ridge Modelling

## Descrizione del task

Il task consiste nella **modellazione 3D del coral garden** presente nel Flume Tank durante il World Championship. Il coral garden è una struttura in pipe PVC da ½ pollice con le seguenti caratteristiche:

- Lunghezza: tra 1 m e 2,5 m
- Larghezza: circa 36 cm
- Altezza: non nota a priori
- **8 target** (quadrati 10 × 10 cm in plastica corrugata colorata) applicati sul PVC

---

## Approccio scelto: Fotogrammetria autonoma

L'approccio principale è la **creazione automatica di un modello 3D tramite fotogrammetria**. Il processo prevede:

1. Il ROV manovra manualmente intorno al coral garden raccogliendo immagini da più angolazioni.
2. Le immagini vengono trasferite al computer della mission station (anche manualmente).
3. Un software di fotogrammetria (es. **Meshroom**, **COLMAP**, **Reality Capture**) elabora le immagini e ricostruisce il modello 3D.
4. Il modello viene importato in un programma CAD per la visualizzazione, la scalatura e le misurazioni.

> È consentito posizionare un oggetto di dimensioni note (es. un righello) vicino al coral garden per facilitare la scalatura. **Attenzione**: tale oggetto conta come debris se non viene rimosso o controllato dal ROV entro la fine del product demonstration time.

---

## Pipeline fotogrammetrica

```
Immagini ROV
     │
     ▼
Software fotogrammetria (Meshroom / COLMAP)
     │
     ▼
Modello 3D (.obj / .ply)
     │
     ▼
Import in CAD (Blender / FreeCAD / Fusion 360)
     │
     ▼
Scalatura con lunghezza vera (fornita dal giudice)
     │
     ▼
Visualizzazione + misura altezza
```

---

## Criteri di punteggio

### Metodo fotogrammetrico (max 40 pt)

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

> **Nota**: i punti vengono assegnati **solo per un metodo**. È tuttavia possibile tentare entrambi: se la fotogrammetria ha successo si ottengono fino a 40 pt; se fallisce, si ricevono comunque fino a 30 pt per il modello manuale.

---

## Requisiti per il product demonstration

- Il modello 3D deve essere **visualizzato su schermo** alla mission station.
- Deve essere **ruotabile** per consentire al giudice di vederlo da qualsiasi angolazione.
- Per la fotogrammetria: devono essere visibili i **target colorati**.
- Per il metodo manuale: le **misure di lunghezza e altezza** devono essere incluse nel modello.

---

## Struttura della cartella

```
Task 1.2/
├── README.md          ← questo file
└── (script / file CAD / immagini ROV da aggiungere)
```

---

## Note operative

- Richiedere la **lunghezza vera** al giudice subito dopo aver fornito la propria misurazione (senza la misura non si ottiene la lunghezza vera e non si può scalare il modello).
- Senza scalatura corretta non è possibile ottenere i punti per la stima dell'altezza.
- Verificare che il software di fotogrammetria riconosca tutti e 8 i target prima della demo.
