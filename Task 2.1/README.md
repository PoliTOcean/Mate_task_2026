# Task 2.1 — Mitigate Invasive Species

## Descrizione del task

Il task consiste nel **contare il numero di granchi invasivi** (*European Green Crab*) presenti in un campione. Le immagini dei granchi sono stampate, plastificate e fissate su un foglio di plastica corrugata **50 × 50 cm**.

Il campione contiene tre specie:

| Specie | Tipo | Da contare? |
|---|---|---|
| *European Green Crab* | Invasiva | ✅ Sì |
| *Rock Crab* | Nativa | ❌ No |
| *Jonah Crab* | Nativa | ❌ No |

Le immagini di riferimento si trovano nella cartella [`crabs/`](crabs/).

---

## Approccio scelto: Image Recognition con YOLOv8

L'approccio scelto è la **rilevazione automatica tramite rete neurale** basata su **YOLOv8** (Ultralytics). Il modello rileva e classifica i granchi nelle immagini acquisite dalla telecamera del ROV.

### Come funziona

1. Il ROV inquadra manualmente il pannello 50 × 50 cm con le immagini dei granchi.
2. Il frame video viene catturato e passato al modello YOLOv8.
3. Il programma disegna un **bounding box** attorno a ogni granchio verde rilevato.
4. Il **conteggio totale** dei *Green Crab* viene mostrato a schermo.
5. I *Rock Crab* e *Jonah Crab* non vengono inclusi nel conteggio né incorniciati.

---

## Struttura della cartella

```
Task 2.1/
├── README.md                    ← questo file
├── best.pt                      ← modello YOLOv8 addestrato
├── crab_counter.py              ← script di inferenza principale
├── train_yolo_colab.ipynb       ← notebook per addestrare il modello (Colab)
├── img_generator_colab.ipynb    ← notebook per generare immagini sintetiche (Colab)
├── dataset.zip                  ← dataset usato per il training
├── crabs/                       ← immagini di riferimento delle tre specie
│   ├── green_crab.jpg
│   ├── rock_crab.jpg
│   └── jonah_crab.png
└── practice/                    ← immagini di test
    ├── sample_1.jpg
    ├── sample_2.jpg
    └── sample_3.jpg
```

---

## Utilizzo

### Prerequisiti

```bash
pip install ultralytics
```

### Esecuzione

```bash
python crab_counter.py
```

Lo script elabora tutte le immagini contenute nella cartella `practice/`, stampa a terminale il conteggio per specie e salva le immagini annotate con i bounding box come `out_<nome_immagine>`.

**Output esempio:**

```
════════════════════════════════════════════════════
   🦀  Crab Detector — 3 immagini
════════════════════════════════════════════════════

  [1/3] sample_1.jpg
        3 green crab (invasive)
        Invasivi: 3
        → .../practice/out_sample_1.jpg
```

> Il modello opera con una **confidenza minima del 50%** (`conf=0.5`). Le immagini annotate vengono salvate automaticamente nella cartella `practice/`.

---

## Training del modello

Il modello `best.pt` è stato addestrato su un dataset custom con le tre classi (`green`, `rock`, `jonah`).

### Dataset

Il dataset è stato preparato con:
- Immagini reali delle tre specie di granchi nelle pose e rotazioni previste dal regolamento.
- Immagini sintetiche generate tramite [`img_generator_colab.ipynb`](img_generator_colab.ipynb), che posiziona le immagini delle tre specie in modo casuale su sfondi variabili simulando il pannello 50 × 50 cm.

### Addestramento

Il training è stato eseguito su Google Colab tramite [`train_yolo_colab.ipynb`](train_yolo_colab.ipynb):

```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")          # backbone leggero
model.train(data="crab_dataset.yaml", epochs=100, imgsz=640)
```

Il modello migliore (per mAP su validation set) viene salvato come `best.pt`.

---

## Criteri di punteggio

| Risultato | Punti |
|---|---|
| Conteggio manuale corretto dei *Green Crab* | 5 pt |
| Conteggio automatico con image recognition | **15 pt** |
| Compilazione del modulo "Invasive Species Reporting Form" | **+5 pt** |
| **Totale massimo** | **20 pt** |

### Requisiti per la demo

- Il video del ROV deve inquadrare l'**intera area 50 × 50 cm**.
- Ogni *Green Crab* deve avere un **bounding box visibile**.
- Il **numero totale** deve essere mostrato a schermo.
- *Rock Crab* e *Jonah Crab* **non** devono avere bounding box.
- Dopo il conteggio, compilare il **Invasive Species Reporting Form** (QR code disponibile alla mission station) e mostrare al giudice la conferma di invio.

> **Attenzione**: è consentito **un solo tentativo** per comunicare il numero di granchi al giudice. Non è possibile tirare ad indovinare.
