"""Ricostruzione 3D del Coral Garden da due viste (fronte + retro).

A partire dai risultati di `final.analyze()` per il lato fronte e il lato retro,
costruisce un modello 3D della struttura:

  - la STRUTTURA in PVC e' un TELAIO A MACROBLOCCHI (vedi frame.py): pochi
    parallelepipedi uniti (ala sx + torre centrale + ala dx + base) scalati a
    (L, H, profondita') misurati dalle foto. Sempre intero e connesso;
  - tutti i target colorati 10x10 cm sono posizionati al loro posto (fronte su
    z=0, retro su z=profondita'), agganciati al tubo piu' vicino.

Il modello e' mostrabile in una finestra interattiva ruotabile (matplotlib 3D)
da proiettare alla mission station, ed e' esportabile come file .obj.

La profondita' (larghezza della struttura) e' un valore fisso noto da
regolamento (~36 cm): con due sole foto non calibrate non ha senso stimarla per
parallasse.
"""

import os
import sys

import numpy as np

# Permette di importare il modulo fratello `frame` anche se model_3d viene
# caricato da un'altra CWD (es. da NEXUS via importlib).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_DEPTH_CM = 36.0
# Lato dei target: da regolamento Task 1.2 sono quadrati 10x10 cm, TUTTI uguali.
# Non usiamo la dimensione rilevata (varia per prospettiva): la fissiamo qui.
TARGET_SIZE_CM = 10.0

# =============================================================================
# Font a segmenti per le QUOTE d'ingombro (testo 3D dentro l'.obj).
# =============================================================================
# Ogni carattere e' una lista di segmenti su una griglia 2D normalizzata:
# x in [0..1] (larghezza glifo), y in [0..2] (altezza glifo). I segmenti
# vengono poi scalati a `height_cm` e collocati su un piano 3D (vedi
# _text_segments). Stile "7 segmenti" per le cifre, abbastanza per leggere
# una misura in qualunque viewer 3D.
_GLYPHS = {
    "0": [(0, 0, 1, 0), (1, 0, 1, 2), (1, 2, 0, 2), (0, 2, 0, 0)],
    "1": [(0.5, 0, 0.5, 2), (0.2, 1.6, 0.5, 2)],
    "2": [(0, 2, 1, 2), (1, 2, 1, 1), (1, 1, 0, 1), (0, 1, 0, 0), (0, 0, 1, 0)],
    "3": [(0, 2, 1, 2), (1, 2, 1, 0), (1, 0, 0, 0), (0, 1, 1, 1)],
    "4": [(0, 2, 0, 1), (0, 1, 1, 1), (1, 2, 1, 0)],
    "5": [(1, 2, 0, 2), (0, 2, 0, 1), (0, 1, 1, 1), (1, 1, 1, 0), (1, 0, 0, 0)],
    "6": [(1, 2, 0, 2), (0, 2, 0, 0), (0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 1)],
    "7": [(0, 2, 1, 2), (1, 2, 0.4, 0)],
    "8": [(0, 0, 1, 0), (1, 0, 1, 2), (1, 2, 0, 2), (0, 2, 0, 0), (0, 1, 1, 1)],
    "9": [(1, 0, 1, 2), (1, 2, 0, 2), (0, 2, 0, 1), (0, 1, 1, 1)],
    ".": [(0.4, 0, 0.6, 0), (0.6, 0, 0.6, 0.2), (0.6, 0.2, 0.4, 0.2), (0.4, 0.2, 0.4, 0)],
    "c": [(1, 1.3, 0.2, 1.3), (0.2, 1.3, 0, 1), (0, 1, 0.2, 0.2),
          (0.2, 0.2, 1, 0.2)],
    "m": [(0, 0, 0, 1.3), (0, 1.3, 0.5, 1.3), (0.5, 1.3, 0.5, 0),
          (0.5, 1.3, 1, 1.3), (1, 1.3, 1, 0)],
    " ": [],
}
# Larghezza nominale di un glifo (in unita' di griglia) e spazio tra glifi.
_GLYPH_W = 1.0
_GLYPH_GAP = 0.4


def _glyph_segments(ch):
    """Segmenti 2D del glifo (lista di (x1,y1,x2,y2)); '?' per ignoti -> vuoto."""
    return _GLYPHS.get(ch, [])


def _text_segments(text, origin, height_cm, right, up):
    """Trasforma una stringa in segmenti 3D ((p1),(p2)) su un piano.

    Args:
        text: stringa da disegnare (cifre, '.', 'c', 'm', spazio).
        origin: (x,y,z) angolo in basso a sinistra del primo glifo, in cm.
        height_cm: altezza dei glifi in cm (la griglia y=0..2 mappa a 0..height).
        right: versore 3D della direzione "destra" del testo (asse x del testo).
        up: versore 3D della direzione "su" del testo (asse y del testo).

    Returns:
        lista di segmenti 3D ((x1,y1,z1),(x2,y2,z2)).
    """
    o = np.asarray(origin, float)
    right = np.asarray(right, float)
    up = np.asarray(up, float)
    s = height_cm / 2.0  # la griglia y va 0..2 -> scala per avere altezza height_cm

    segs = []
    cursor = 0.0  # avanzamento orizzontale in unita' di griglia
    for ch in text:
        for (x1, y1, x2, y2) in _glyph_segments(ch):
            p1 = o + (cursor + x1) * s * right + y1 * s * up
            p2 = o + (cursor + x2) * s * right + y2 * s * up
            segs.append((tuple(p1), tuple(p2)))
        cursor += _GLYPH_W + _GLYPH_GAP
    return segs


def _text_width_cm(text, height_cm):
    """Larghezza totale (cm) della stringa con il font a segmenti."""
    s = height_cm / 2.0
    n = len(text)
    if n == 0:
        return 0.0
    return (n * _GLYPH_W + (n - 1) * _GLYPH_GAP) * s


def _dimension_segments(p_start, p_end, offset, text, text_height_cm,
                        right, up, text_side=1.0):
    """Quota in stile disegno tecnico fra p_start e p_end, come segmenti 3D.

    Costruisce: linea di quota (traslata di `offset` fuori dall'ingombro), due
    linee di estensione dagli estremi reali alla linea di quota, due tacche a
    45 gradi agli estremi, e il testo del valore centrato sulla linea.

    `right`/`up` orientano il GLIFO e devono restare nel verso "leggibile"
    (up verso l'alto reale), altrimenti le cifre escono specchiate/capovolte.
    `text_side` (+1/-1) sceglie solo da che parte della linea mettere il testo,
    senza ruotarlo: usalo per spingere il testo lontano dalla struttura.

    Args:
        p_start, p_end: estremi REALI della misura (cm).
        offset: vettore 3D che sposta la linea di quota fuori dalla struttura.
        text: etichetta da scrivere (es. "183.3 cm").
        text_height_cm: altezza dei caratteri.
        right, up: versori (leggibili) del piano su cui disegnare il testo.
        text_side: +1 mette il testo dal lato +up della linea, -1 dal lato -up.

    Returns:
        lista di segmenti 3D.
    """
    a = np.asarray(p_start, float)
    b = np.asarray(p_end, float)
    off = np.asarray(offset, float)
    right = np.asarray(right, float)
    up = np.asarray(up, float)
    a2, b2 = a + off, b + off  # estremi della linea di quota

    segs = [
        (tuple(a2), tuple(b2)),   # linea di quota
        (tuple(a), tuple(a2)),    # estensione lato start
        (tuple(b), tuple(b2)),    # estensione lato end
    ]

    # Tacche a 45 gradi agli estremi (lungo right+up del piano del testo).
    tick = text_height_cm * 0.5
    diag = (right + up)
    diag = diag / (np.linalg.norm(diag) + 1e-9) * tick
    segs.append((tuple(a2 - diag), tuple(a2 + diag)))
    segs.append((tuple(b2 - diag), tuple(b2 + diag)))

    # Testo centrato sulla linea di quota, spostato dal lato scelto (text_side)
    # ma SEMPRE orientato in modo leggibile (right/up invariati).
    mid = (a2 + b2) / 2.0
    w = _text_width_cm(text, text_height_cm)
    if text_side >= 0:
        base = mid + text_height_cm * 0.4 * up          # testo sopra la linea
    else:
        base = mid - text_height_cm * 1.4 * up          # testo sotto la linea
    text_origin = base - (w / 2.0) * right
    segs += _text_segments(text, text_origin, text_height_cm, right, up)
    return segs


def build_dimension_lines(model):
    """Segmenti 3D delle tre quote d'ingombro L/H/P del modello.

    Disegna le quote FUORI dall'ingombro cosi' non si sovrappongono alla
    struttura. Riutilizzabile sia dall'export .obj sia dall'anteprima 3D.

    Returns:
        lista di segmenti 3D ((x1,y1,z1),(x2,y2,z2)).
    """
    L = model["length_cm"]
    H = model["height_cm"]
    D = model["depth_cm"]
    th = max(4.0, 0.06 * max(L, H, 1.0))  # altezza testo proporzionata
    # Distacco delle quote dall'ingombro: ben staccate cosi' linee di quota,
    # estensioni e cifre NON si compenetrano con i tubi della struttura.
    gap = max(th * 3.0, 0.18 * max(L, H, 1.0))

    ex = np.array([1.0, 0.0, 0.0])
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])

    segs = []

    # LUNGHEZZA: lungo X, ben sotto la base (offset -Y), testo sul piano frontale XY.
    # Glifo leggibile (up=+ey) col testo spinto SOTTO la linea di quota.
    segs += _dimension_segments(
        (0.0, 0.0, 0.0), (L, 0.0, 0.0),
        offset=np.array([0.0, -gap, 0.0]),
        text=f"{L:.1f} cm", text_height_cm=th, right=ex, up=ey, text_side=-1.0)

    # ALTEZZA: lungo Y, a DESTRA della struttura (offset +X), lato piu' libero.
    # Testo ruotato di 90 gradi come quota verticale leggibile: right=+ey (cifre
    # verso l'alto), up=-ex (il "sopra" dei glifi guarda la struttura, cosi' NON
    # escono specchiati). text_side=-1 lo spinge comunque a destra, fuori.
    segs += _dimension_segments(
        (L, 0.0, 0.0), (L, H, 0.0),
        offset=np.array([gap, 0.0, 0.0]),
        text=f"{H:.1f} cm", text_height_cm=th, right=ey, up=-ex, text_side=-1.0)

    # PROFONDITA': lungo Z, portata FUORI a sinistra (offset -X) e in basso, cosi'
    # non si accavalla con la quota Lunghezza vicino all'origine. Testo sul piano
    # laterale YZ, leggibile (up=+ey), spinto sotto la linea.
    segs += _dimension_segments(
        (0.0, 0.0, 0.0), (0.0, 0.0, D),
        offset=np.array([-gap, 0.0, 0.0]),
        text=f"{D:.1f} cm", text_height_cm=th, right=ez, up=ey, text_side=-1.0)

    return segs


def _bgr_to_mpl(color_bgr):
    """Converte un colore BGR (OpenCV) in una tupla RGB 0..1 per matplotlib."""
    b, g, r = color_bgr
    return (r / 255.0, g / 255.0, b / 255.0)


def build_model(front_result, back_result, depth_cm=DEFAULT_DEPTH_CM):
    """Fonde i risultati di fronte e retro in un'unica struttura dati 3D.

    Args:
        front_result: dict ritornato da analyze() per la foto del fronte.
        back_result: dict ritornato da analyze() per la foto del retro
            (puo' essere None se si dispone di una sola vista).
        depth_cm: profondita' della struttura (larghezza nota da regolamento).

    Returns:
        dict con chiavi:
          length_cm, height_cm, depth_cm,
          tubes: lista di tubi 3D ((x1,y1,z1),(x2,y2,z2)) in cm,
          targets: lista di dict {x_cm, y_cm, z_cm, size_cm, color, side}.
    """
    import frame

    sides = [("front", front_result, 0.0)]
    if back_result is not None:
        sides.append(("back", back_result, depth_cm))

    lengths = [s[1]["length_cm"] for s in sides if s[1].get("length_cm")]
    heights = [s[1]["height_cm"] for s in sides if s[1].get("height_cm")]
    length_cm = max(lengths) if lengths else 0.0
    height_cm = max(heights) if heights else 0.0

    # Telaio a MACROBLOCCHI (topologia nota dal manuale) scalato alle dimensioni
    # misurate: ala sx + torre centrale + ala dx + base, sempre intero e connesso.
    tubes = frame.build_frame(length_cm, height_cm, depth_cm)

    # Target: X/Y reale rilevata dalle foto, appoggiato sulla faccia esterna del
    # proprio lato (fronte/retro), agganciato ai tubi di quel piano e sporgente
    # leggermente in fuori cosi' e' ben visibile sulla struttura.
    targets = []
    for side_name, res, _z in sides:
        for t in res.get("targets", []):
            # Tutti i target hanno lato fisso 10x10 cm (regolamento), non la
            # dimensione rilevata che varia con la prospettiva.
            x_s, y_s, z_s = frame.place_target(
                t["x_cm"], t["y_cm"], side_name, depth_cm, tubes)
            targets.append({
                "x_cm": x_s,
                "y_cm": y_s,
                "z_cm": z_s,
                "size_cm": TARGET_SIZE_CM,
                "color": _bgr_to_mpl(t["color_bgr"]),
                "side": side_name,
            })

    return {
        "length_cm": length_cm,
        "height_cm": height_cm,
        "depth_cm": depth_cm,
        "tubes": tubes,
        "targets": targets,
    }


def _target_quad(t):
    """Restituisce i 4 vertici 3D di un quadrato target, sul piano del suo lato."""
    half = t["size_cm"] / 2.0
    x, y, z = t["x_cm"], t["y_cm"], t["z_cm"]
    return [
        (x - half, y - half, z),
        (x + half, y - half, z),
        (x + half, y + half, z),
        (x - half, y + half, z),
    ]


def show_interactive(model, block=True):
    """Apre una finestra 3D ruotabile col telaio di tubi e i target colorati.

    Pensata per la demo: il giudice puo' ruotare il modello col mouse e vedere
    il graticcio di tubi della struttura, tutti i target su entrambi i lati e le
    misure nel titolo.
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

    L, H, D = model["length_cm"], model["height_cm"], model["depth_cm"]

    fig = plt.figure(figsize=(11, 7))
    ax = fig.add_subplot(111, projection="3d")

    # Telaio di tubi (linee spesse).
    if model["tubes"]:
        ax.add_collection3d(Line3DCollection(
            model["tubes"], colors="0.25", linewidths=3.0))

    # Target come quadrati pieni col loro colore reale.
    quads = [_target_quad(t) for t in model["targets"]]
    facecolors = [t["color"] for t in model["targets"]]
    if quads:
        ax.add_collection3d(Poly3DCollection(
            quads, facecolors=facecolors, edgecolors="black", linewidths=0.8))

    # Quote d'ingombro L/H/P (stesse linee dell'.obj) come linee blu sottili.
    dim_segments = build_dimension_lines(model)
    if dim_segments:
        ax.add_collection3d(Line3DCollection(
            dim_segments, colors="tab:blue", linewidths=1.2))

    ax.set_xlim(0, max(L, 1))
    ax.set_ylim(0, max(H, 1))
    ax.set_zlim(0, max(D, 1))
    ax.set_box_aspect((max(L, 1), max(H, 1), max(D, 1)))  # proporzioni reali
    ax.set_xlabel("Lunghezza (cm)")
    ax.set_ylabel("Altezza (cm)")
    ax.set_zlabel("Profondita' (cm)")

    # Vista iniziale FRONTALE (lunghezza in orizzontale, altezza in verticale,
    # come la foto del coral garden); resta comunque ruotabile col mouse.
    ax.view_init(elev=90, azim=-90)

    n_front = sum(1 for t in model["targets"] if t["side"] == "front")
    n_back = sum(1 for t in model["targets"] if t["side"] == "back")
    ax.set_title(
        f"Coral Garden — L={L:.1f} cm  H={H:.1f} cm  P={D:.1f} cm\n"
        f"Target: {len(model['targets'])} totali "
        f"({n_front} fronte + {n_back} retro)  |  Tubi: {len(model['tubes'])}")

    plt.tight_layout()
    plt.show(block=block)
    return fig


def _tube_box(p1, p2, radius_cm):
    """Vertici (8) e facce (6 quad) di un tubo come parallelepipedo sottile.

    Costruisce un box di sezione 2*radius attorno al segmento p1-p2. I tubi
    devono essere SOLIDI (facce), non linee: i viewer CAD (Autodesk, Fusion,
    SolidWorks) renderizzano le facce ma ignorano le primitive linea `l`.
    """
    p1 = np.asarray(p1, float)
    p2 = np.asarray(p2, float)
    axis = p2 - p1
    n = np.linalg.norm(axis)
    if n == 0:
        axis = np.array([1.0, 0.0, 0.0])
        n = 1.0
    axis /= n
    # Due assi perpendicolari all'asse del tubo.
    ref = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(axis, ref); u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    r = radius_cm
    corners = [(-r, -r), (r, -r), (r, r), (-r, r)]
    verts = []
    for base in (p1, p2):
        for (a, b) in corners:
            verts.append(tuple(base + a * u + b * v))
    # Facce del box (indici locali 0-based): 4 laterali + 2 tappi.
    faces = [
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        (0, 1, 2, 3), (4, 5, 6, 7),
    ]
    return verts, faces


def export_mesh(model, path, tube_radius_cm=0.8, dimensions=True):
    """Esporta il modello come file .obj (testo, nessuna dipendenza extra).

    I tubi sono SOLIDI (parallelepipedi sottili, sezione ~1/2") e i target sono
    quad a DOPPIA faccia (visibili da entrambi i lati): tutto come facce `f`,
    cosi' i viewer/CAD (Autodesk Viewer, Fusion 360, SolidWorks, MeshLab,
    Blender) mostrano la struttura completa da qualunque angolo.

    Se `dimensions` e' True, aggiunge le QUOTE d'ingombro L/H/P (lunghezza,
    altezza, profondita') come box SOLIDI sottili (non primitive linea `l`):
    Autodesk Viewer e altri viewer ignorano le `l`, quindi linee di quota e
    cifre vengono "ingrossate" in parallelepipedi cosi' sono sempre visibili.
    """
    lines = ["# Coral Garden 3D model — generato da model_3d.export_mesh"]
    vertices = []
    faces = []   # tuple di indici 1-based

    def add_vertex(p):
        vertices.append(p)
        return len(vertices)  # 1-based

    def add_box(p1, p2, radius):
        """Aggiunge un box solido (6 facce) attorno al segmento p1-p2."""
        vb, fb = _tube_box(p1, p2, radius)
        base = len(vertices)
        for p in vb:
            add_vertex(p)
        for f in fb:
            faces.append(tuple(base + i + 1 for i in f))

    # Tubi come box solidi.
    for (p1, p2) in model["tubes"]:
        add_box(p1, p2, tube_radius_cm)

    # Target come quad DOPPIO (faccia + faccia opposta): i viewer fanno backface
    # culling, quindi un quad singolo sparisce guardandolo dal lato "sbagliato"
    # (era il caso dei target visti dal retro). Emettere anche il quad con i
    # vertici invertiti li rende opachi da entrambi i lati.
    for t in model["targets"]:
        idx = [add_vertex(p) for p in _target_quad(t)]
        faces.append(tuple(idx))
        faces.append(tuple(reversed(idx)))

    # Quote d'ingombro come box solidi sottili (linee di quota + cifre del testo).
    dim_segments = build_dimension_lines(model) if dimensions else []
    dim_radius = max(0.15, 0.004 * max(model["length_cm"], model["height_cm"], 1.0))
    for (p1, p2) in dim_segments:
        add_box(p1, p2, dim_radius)

    for x, y, z in vertices:
        lines.append(f"v {x:.3f} {y:.3f} {z:.3f}")
    for f in faces:
        lines.append("f " + " ".join(str(i) for i in f))

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    n_tubes = len(model["tubes"])
    print(f"Modello 3D esportato in '{path}' "
          f"({len(vertices)} vertici, {len(faces)} facce; "
          f"{n_tubes} tubi solidi + {len(model['targets'])} target + "
          f"{len(dim_segments)} segmenti di quota solidi).")
    return path
