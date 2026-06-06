# MATE ROV 2026 — Tasks

**Team:** PoliTOcean — Politecnico di Torino
**Competizione:** MATE ROV World Championship 2026 — Explorer Class

---

## Panoramica

Questa repository raccoglie il codice e la documentazione per i **task lato Control Station** del campionato MATE ROV 2026. Entrambi i task si svolgono nel Flume Tank e richiedono l'uso del ROV combinato con elaborazione software a terra.

---

## Task

### [Task 1.2 — Coral Garden Ridge Modelling](Task%201.2/README.md)

> **Obiettivo:** misurare e creare un modello 3D del coral garden nel Flume Tank.

Il coral garden è una struttura in PVC (1–2,5 m × 36 cm, altezza ignota) con **8 target colorati** 10 × 10 cm. Il task prevede due approcci alternativi:

| Approccio | Metodo | Max punti |
|---|---|---|
| **CV automatico** | Computer Vision (OpenCV) + CAD SolidWorks | **40 pt** |
| **Manuale** | Misurazioni + modello CAD | **30 pt** |

L'approccio del team è la **misurazione automatica tramite computer vision**: il ROV posiziona un righello arancione da 50 cm come riferimento metrico e acquisisce una foto della struttura. Lo script `final.py` calcola la scala pixel/cm dal righello, rileva i target colorati, misura lunghezza e altezza dei tubi PVC e scrive i valori in `equations.txt`, che SolidWorks legge automaticamente per scalare il modello CAD.

📁 [`Task 1.2/`](Task%201.2/)

---

### [Task 2.1 — Mitigate Invasive Species](Task%202.1/README.md)

> **Obiettivo:** contare automaticamente i granchi invasivi *European Green Crab* in un campione 50 × 50 cm tramite image recognition.

Il campione contiene immagini di tre specie (Green Crab, Rock Crab, Jonah Crab). Il team ha addestrato un modello **YOLOv8** per rilevare e contare solo i granchi invasivi.

| Approccio | Metodo | Max punti |
|---|---|---|
| **Automatico** | YOLOv8 image recognition | **15 pt** |
| **Manuale** | Conteggio visivo | 5 pt |
| Reporting form | Compilazione form online | **+5 pt** |

📁 [`Task 2.1/`](Task%202.1/)

---

## Riepilogo punteggi

| Task | Descrizione | Max punti |
|---|---|---|
| 1.2 | Coral Garden Modelling (computer vision + CAD) | 40 pt |
| 2.1 | Invasive Species (image recognition + form) | 20 pt |
| **Totale CS** | | **60 pt** |

---

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Object detection | [YOLOv8](https://github.com/ultralytics/ultralytics) (Ultralytics) |
| Computer vision | [OpenCV](https://opencv.org/) + NumPy |
| CAD | SolidWorks (equazioni parametriche) |
| Training | Google Colab + PyTorch |
| Linguaggio | Python 3 |

---

## Struttura della repository

```
Task CS/
├── README.md              ← questo file
├── Task 1.2/
│   ├── README.md          ← documentazione computer vision
│   ├── final.py           ← script principale CV
│   ├── target.py          ← versione precedente
│   ├── rilevatore_target.py ← prototipo iniziale
│   ├── equations.txt      ← output misure → SolidWorks
│   ├── Coral garden (CAD).SLDPRT ← modello SolidWorks
│   ├── righello.jpg       ← immagine di test
│   ├── nuova.jpg          ← immagine di test
│   ├── Coral garden.zip
│   └── colar_garden.zip
└── Task 2.1/
    ├── README.md          ← documentazione crab detector
    ├── best.pt            ← modello YOLOv8 addestrato
    ├── crab_counter.py    ← script di inferenza
    ├── train_yolo_colab.ipynb
    ├── img_generator_colab.ipynb
    ├── dataset.zip
    ├── crabs/             ← immagini di riferimento specie
    └── practice/          ← immagini di test
```

---

## Setup

```bash
# Crea e attiva il virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# Installa le dipendenze
pip install -r requirements.txt
```

## Avvio rapido

### Task 1.2 — Coral Garden CV

```bash
python "Task 1.2/final.py"
```

### Task 2.1 — Crab Detector

```bash
python "Task 2.1/crab_counter.py"
```
