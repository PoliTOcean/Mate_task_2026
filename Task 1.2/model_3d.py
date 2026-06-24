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

    ax.set_xlim(0, max(L, 1))
    ax.set_ylim(0, max(H, 1))
    ax.set_zlim(0, max(D, 1))
    ax.set_box_aspect((max(L, 1), max(H, 1), max(D, 1)))  # proporzioni reali
    ax.set_xlabel("Lunghezza (cm)")
    ax.set_ylabel("Altezza (cm)")
    ax.set_zlabel("Profondita' (cm)")

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


def export_mesh(model, path, tube_radius_cm=0.8):
    """Esporta il modello come file .obj (testo, nessuna dipendenza extra).

    I tubi sono SOLIDI (parallelepipedi sottili, sezione ~1/2") e i target sono
    facce quad: tutto come facce `f`, cosi' i viewer/CAD (Autodesk Viewer,
    Fusion 360, SolidWorks, MeshLab, Blender) mostrano la struttura completa.
    """
    lines = ["# Coral Garden 3D model — generato da model_3d.export_mesh"]
    vertices = []
    faces = []   # tuple di indici 1-based

    def add_vertex(p):
        vertices.append(p)
        return len(vertices)  # 1-based

    # Tubi come box solidi.
    for (p1, p2) in model["tubes"]:
        vb, fb = _tube_box(p1, p2, tube_radius_cm)
        base = len(vertices)
        for p in vb:
            add_vertex(p)
        for f in fb:
            faces.append(tuple(base + i + 1 for i in f))

    # Target come quad.
    for t in model["targets"]:
        idx = [add_vertex(p) for p in _target_quad(t)]
        faces.append(tuple(idx))

    for x, y, z in vertices:
        lines.append(f"v {x:.3f} {y:.3f} {z:.3f}")
    for f in faces:
        lines.append("f " + " ".join(str(i) for i in f))

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    n_tubes = len(model["tubes"])
    print(f"Modello 3D esportato in '{path}' "
          f"({len(vertices)} vertici, {len(faces)} facce; "
          f"{n_tubes} tubi solidi + {len(model['targets'])} target).")
    return path
