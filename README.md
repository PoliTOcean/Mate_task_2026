# MATE ROV 2026 — Computer Science Tasks

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
| **Autonomo** | Fotogrammetria (Meshroom / COLMAP) + CAD | **40 pt** |
| **Manuale** | Misurazioni + modello CAD | **30 pt** |

L'approccio principale del team è la **fotogrammetria**: il ROV raccoglie immagini del coral garden da più angolazioni, un software di fotogrammetria ricostruisce il modello 3D, che viene poi scalato con la lunghezza fornita dal giudice per ricavarne anche l'altezza.

📁 [`Task 1.2/`](Task%201.2/) — *al momento in sviluppo*

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
| 1.2 | Coral Garden Modelling (fotogrammetria) | 40 pt |
| 2.1 | Invasive Species (image recognition + form) | 20 pt |
| **Totale CS** | | **60 pt** |

---

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Object detection | [YOLOv8](https://github.com/ultralytics/ultralytics) (Ultralytics) |
| Fotogrammetria | [Meshroom](https://alicevision.org/) / [COLMAP](https://colmap.github.io/) |
| Training | Google Colab + PyTorch |
| Linguaggio | Python 3 |

---

## Struttura della repository

```
Task CS/
├── README.md              ← questo file
├── Task 1.2/
│   └── README.md          ← documentazione fotogrammetria
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

## Avvio rapido — Task 2.1

```bash
# Installa le dipendenze
pip install ultralytics

# Lancia il crab detector sulle immagini in practice/
python "Task 2.1/crab_counter.py"
```
