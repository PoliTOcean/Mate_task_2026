"""Telaio del Coral Garden a MACROBLOCCHI (parallelepipedi uniti).

La topologia del coral garden e' NOTA (disegno del manuale MATE 2026): cambiano
solo le DIMENSIONI. Invece di curare ogni singolo tubo (fragile, lasciava
frammenti), la struttura e' composta da pochi BLOCCHI 3D (box wireframe) uniti:

  - ALA SINISTRA  : box basso  (~0 -> 28% L, alto y_low)
  - TORRE CENTRALE: box alto   (~30% -> 78% L, alto y=H)
  - ALA DESTRA    : box medio  (~78% -> 100% L, alto y_mid)
  - BASE          : box piatto che corre sotto tutto, unendo i blocchi

Ogni box e' un parallelepipedo (12 spigoli) sempre connesso; l'insieme dei box
forma una struttura unica, intera e riconoscibile. Tutto e' scalato a (L,H,D)
misurati dalle foto; i target rilevati vengono appoggiati al tubo piu' vicino
(snap_target_to_frame).

Le frazioni X_*/Y_* qui sotto sono tarate sul disegno/foto: ritoccale se sul
campo la struttura risulta leggermente diversa.
"""

import numpy as np

# --- Frazioni orizzontali (di L) dei blocchi (ATTACCATI: condividono i bordi) ---
X_L0 = 0.00   # estremo sinistro (ala sx)
X_L1 = 0.29   # fine ala sinistra = inizio torre
X_T1 = 0.79   # fine torre = inizio ala destra
X_R1 = 1.00   # estremo destro
# Alias di leggibilita': i blocchi combaciano sui bordi condivisi.
X_T0 = X_L1   # torre inizia dove finisce l'ala sx
X_R0 = X_T1   # ala dx inizia dove finisce la torre

# --- Frazioni verticali (di H) ---
Y_LOW = 0.35   # altezza ala sinistra
Y_MID = 0.52   # altezza ala destra
Y_TOP = 1.00   # altezza torre
Y_BASE = 0.12  # spessore della base piatta che unisce i blocchi


def _box_edges(x0, x1, y0, y1, z0, z1):
    """12 spigoli di un parallelepipedo come tubi ((p1),(p2))."""
    v = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),  # faccia z0
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),  # faccia z1
    ]
    idx = [
        (0, 1), (1, 2), (2, 3), (3, 0),   # contorno z0
        (4, 5), (5, 6), (6, 7), (7, 4),   # contorno z1
        (0, 4), (1, 5), (2, 6), (3, 7),   # spigoli di profondita'
    ]
    return [(v[a], v[b]) for a, b in idx]


def build_frame(length_cm, height_cm, depth_cm):
    """Costruisce il telaio a macroblocchi scalato alle dimensioni date.

    Returns:
        tubes: lista di tubi ((x1,y1,z1),(x2,y2,z2)) in cm, struttura connessa.
    """
    L, H, D = length_cm, height_cm, depth_cm
    z0, z1 = 0.0, D

    yL, yM, yT, yBase = Y_LOW * H, Y_MID * H, Y_TOP * H, Y_BASE * H

    tubes = []
    # Base piatta che unisce tutti i blocchi (corre per tutta la lunghezza).
    tubes += _box_edges(X_L0 * L, X_R1 * L, 0.0, yBase, z0, z1)
    # Ala sinistra (box basso).
    tubes += _box_edges(X_L0 * L, X_L1 * L, 0.0, yL, z0, z1)
    # Torre centrale (box alto).
    tubes += _box_edges(X_T0 * L, X_T1 * L, 0.0, yT, z0, z1)
    # Ala destra (box medio).
    tubes += _box_edges(X_R0 * L, X_R1 * L, 0.0, yM, z0, z1)

    return tubes


def _closest_point_on_segment(p, a, b):
    """Punto piu' vicino a p sul segmento a-b (tutto in 3D)."""
    p, a, b = np.asarray(p, float), np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    denom = float(ab @ ab)
    if denom == 0.0:
        return a, float(np.linalg.norm(p - a))
    t = float((p - a) @ ab) / denom
    t = max(0.0, min(1.0, t))
    q = a + t * ab
    return q, float(np.linalg.norm(p - q))


def snap_target_to_frame(point, tubes, max_snap_cm=None):
    """Aggancia un target al punto piu' vicino del telaio.

    Args:
        point: (x,y,z) del centro del target in cm.
        tubes: lista di tubi del telaio.
        max_snap_cm: se impostato, non sposta il target oltre questa distanza;
            None = aggancia sempre.

    Returns:
        (x,y,z) del punto agganciato (o l'originale se oltre max_snap_cm).
    """
    best_q, best_d = None, float("inf")
    for (a, b) in tubes:
        q, d = _closest_point_on_segment(point, a, b)
        if d < best_d:
            best_q, best_d = q, d
    if best_q is None:
        return point
    if max_snap_cm is not None and best_d > max_snap_cm:
        return point
    return (float(best_q[0]), float(best_q[1]), float(best_q[2]))


def place_target(x_cm, y_cm, side, depth_cm, tubes, out_cm=1.5, z_tol=8.0):
    """Posiziona un target sulla faccia esterna del suo lato, attaccato ai tubi.

    Mantiene la X/Y reale rilevata dalla foto, ma:
      - lo aggancia in (x,y) SOLO ai tubi sul piano del suo lato (fronte z~=0 o
        retro z~=depth), cosi' non viene tirato verso tubi interni;
      - lo fa sporgere di out_cm verso l'esterno, cosi' il quadrato e' ben
        visibile appoggiato alla struttura (fronte: z<0; retro: z>depth).

    Returns:
        (x, y, z) del centro del quadrato target.
    """
    z_side = 0.0 if side == "front" else depth_cm
    # Solo i tubi che giacciono sul piano del lato (entro z_tol).
    plane_tubes = [(a, b) for (a, b) in tubes
                   if abs(a[2] - z_side) <= z_tol and abs(b[2] - z_side) <= z_tol]
    if plane_tubes:
        x_s, y_s, _z = snap_target_to_frame((x_cm, y_cm, z_side), plane_tubes)
    else:
        x_s, y_s = x_cm, y_cm
    z = z_side - out_cm if side == "front" else z_side + out_cm
    return (x_s, y_s, z)
