"""Telaio del Coral Garden a MACROBLOCCHI (parallelepipedi uniti).

La topologia del coral garden e' NOTA (disegno del manuale MATE 2026): cambiano
solo le DIMENSIONI. Invece di curare ogni singolo tubo (fragile, lasciava
frammenti), la struttura e' composta da pochi BLOCCHI 3D (box wireframe) uniti:

  - ALA SINISTRA  : box basso  (~0 -> 29% L, alto y_low)
  - TORRE CENTRALE: box alto   (~29% -> 79% L, alto y=H)
  - ALA DESTRA    : box medio  (~79% -> 100% L, alto y_mid)

I tre box sono ADIACENTI (condividono i bordi verticali) e poggiano a y=0, quindi
i loro bordi inferiori formano gia' la base continua: nessun box-base separato.
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

    yL, yM, yT = Y_LOW * H, Y_MID * H, Y_TOP * H

    # Tre blocchi adiacenti (condividono i bordi verticali) che poggiano a y=0:
    # i loro bordi inferiori formano gia' la base continua per tutta la
    # lunghezza, quindi NON serve un box-base separato (evita la doppia linea
    # orizzontale in basso).
    tubes = []
    tubes += _box_edges(X_L0 * L, X_L1 * L, 0.0, yL, z0, z1)   # ala sinistra (basso)
    tubes += _box_edges(X_T0 * L, X_T1 * L, 0.0, yT, z0, z1)   # torre centrale (alto)
    tubes += _box_edges(X_R0 * L, X_R1 * L, 0.0, yM, z0, z1)   # ala destra (medio)

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


def place_target(x_cm, y_cm, side, depth_cm, tubes=None, out_cm=1.5):
    """Posiziona un target rispettando la posizione REALE rilevata dalla foto.

    Mantiene la X/Y misurata cosi' com'e' (NON la sposta su un tubo: snappare
    falsava la posizione tirando i target ai bordi/alla cima). Fissa solo z sul
    piano del lato (fronte z=0, retro z=depth) e lo fa sporgere di out_cm verso
    l'esterno, cosi' il quadrato e' ben visibile sulla faccia della struttura.

    `tubes` e' accettato per compatibilita' ma non usato.

    Returns:
        (x, y, z) del centro del quadrato target.
    """
    z_side = 0.0 if side == "front" else depth_cm
    z = z_side - out_cm if side == "front" else z_side + out_cm
    return (float(x_cm), float(y_cm), z)
