"""Task 2.2 — Iceberg Threat Level.

Calcolo PURO (niente CV, niente modello): dato un iceberg (posizione, heading,
keel depth) determina il livello di minaccia — verde / giallo / rosso — per le 4
piattaforme petrolifere a coordinate fisse da regolamento, sia per la piattaforma
di superficie sia per gli asset subsea.

La funzione `evaluate()` è pura e testabile; importare questo modulo non ha
side-effect. La demo CLI è sotto `if __name__ == "__main__"`.
"""

import math

# Coordinate FISSE da regolamento (NON sono input).
# Le profondità nel manuale sono negative: qui memorizzate come positive.
PLATFORMS = [
    {"name": "Hibernia",   "lat": 43.7504, "lon": -48.7819, "depth_m": 78},
    {"name": "Sea Rose",   "lat": 46.7895, "lon": -48.1417, "depth_m": 107},
    {"name": "Terra Nova", "lat": 46.4,    "lon": -48.4,    "depth_m": 91},
    {"name": "Hebron",     "lat": 46.544,  "lon": -48.498,  "depth_m": 93},
]


def _passing_distance_nm(ice_lat, ice_lon, heading_deg, p_lat, p_lon,
                         forward_only=False):
    """Closest point of approach (CPA) in miglia nautiche.

    Proiezione planare locale (equirettangolare) centrata sull'iceberg, con
    1 minuto di latitudine = 1 NM. L'iceberg è nell'origine e si muove lungo
    l'heading (bearing bussola: 0°=Nord, 90°=Est, orario).

    Per default usa la retta infinita di moto (CPA indipendente dal verso),
    interpretazione standard del regolamento. Con `forward_only=True`, se la
    piattaforma cade "dietro" l'iceberg si usa la distanza corrente invece
    della perpendicolare (da abilitare solo se gli Iceberg track practice
    examples lo richiedono).
    """
    lat0 = math.radians(ice_lat)
    x = (p_lon - ice_lon) * 60.0 * math.cos(lat0)   # NM verso Est
    y = (p_lat - ice_lat) * 60.0                     # NM verso Nord
    th = math.radians(heading_deg)
    dx, dy = math.sin(th), math.cos(th)              # versore direzione (Est, Nord)

    if forward_only and (x * dx + y * dy) < 0:
        # La piattaforma è dietro l'iceberg: il punto più vicino lungo la
        # semiretta in avanti è la posizione attuale dell'iceberg.
        return math.hypot(x, y)

    # d è unitario -> il prodotto vettoriale 2D è la distanza perpendicolare.
    return abs(x * dy - y * dx)


def _surface_threat(passing_nm, keel_ratio):
    """Minaccia alla piattaforma di SUPERFICIE (regole in ordine)."""
    if keel_ratio >= 1.10:   # regola del 110%: si arena prima di arrivare
        return "green"
    if passing_nm < 5:
        return "red"
    if passing_nm <= 10:
        return "yellow"
    return "green"


def _subsea_threat(passing_nm, keel_ratio):
    """Minaccia agli asset SUBSEA (regole in ordine)."""
    if passing_nm > 25:      # fuori dai 25 NM: nessuna minaccia
        return "green"
    if keel_ratio >= 1.10:   # si arena prima
        return "green"
    if keel_ratio >= 0.90:   # pericolo critico
        return "red"
    if keel_ratio >= 0.70:   # può impattare il fondale
        return "yellow"
    return "green"


def evaluate(ice_lat, ice_lon, heading_deg, keel_depth_m, forward_only=False):
    """Valuta la minaccia dell'iceberg per ognuna delle 4 piattaforme.

    Args:
        ice_lat, ice_lon: posizione dell'iceberg (gradi decimali).
        heading_deg: rotta dell'iceberg (bearing bussola, 0°=Nord, orario).
        keel_depth_m: profondità della chiglia dell'iceberg (m, positiva).
        forward_only: vedi `_passing_distance_nm` (default False).

    Returns:
        dict con keys:
          ok (bool), platforms (list di dict con name, passing_distance_nm,
          water_depth_m, keel_ratio, surface_threat, subsea_threat).
    """
    keel = abs(float(keel_depth_m))
    out = []
    for pf in PLATFORMS:
        d = _passing_distance_nm(
            ice_lat, ice_lon, heading_deg, pf["lat"], pf["lon"],
            forward_only=forward_only,
        )
        ratio = keel / pf["depth_m"]
        out.append({
            "name": pf["name"],
            "passing_distance_nm": round(d, 2),
            "water_depth_m": pf["depth_m"],
            "keel_ratio": round(ratio, 3),
            "surface_threat": _surface_threat(d, ratio),
            "subsea_threat":  _subsea_threat(d, ratio),
        })
    return {"ok": True, "platforms": out}


# --- Colori ANSI (solo per l'output CLI) ---
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_CYAN  = "\033[36m"
_WHITE = "\033[97m"
_THREAT_COLOR = {
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
}


def _color(threat):
    return f"{_THREAT_COLOR[threat]}{threat:<6}{_RESET}"


def _run_cli():
    # Esempio dimostrativo: iceberg che punta dritto verso Terra Nova.
    ice_lat, ice_lon, heading, keel = 46.4, -48.5, 90.0, 95.0
    res = evaluate(ice_lat, ice_lon, heading, keel)

    print(f"\n{_BOLD}{_CYAN}{'═' * 60}{_RESET}")
    print(f"{_BOLD}{_CYAN}   🧊  Iceberg Threat Level{_RESET}")
    print(f"{_BOLD}{_CYAN}{'═' * 60}{_RESET}")
    print(f"  iceberg: lat={ice_lat}, lon={ice_lon}, heading={heading}°, "
          f"keel={keel} m\n")
    print(f"  {_BOLD}{_WHITE}{'Platform':<12}{'CPA (NM)':>10}"
          f"{'ratio':>8}   {'surface':<8}{'subsea':<8}{_RESET}")
    print(f"  {'-' * 54}")
    for p in res["platforms"]:
        print(f"  {p['name']:<12}{p['passing_distance_nm']:>10}"
              f"{p['keel_ratio']:>8}   "
              f"{_color(p['surface_threat'])}  {_color(p['subsea_threat'])}")
    print(f"{_BOLD}{_CYAN}{'═' * 60}{_RESET}\n")


if __name__ == "__main__":
    _run_cli()
