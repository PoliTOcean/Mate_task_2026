"""Task 2.5 — eDNA Frequency Calculator.

Calcolo PURO: ricevuti i conteggi delle 10 specie (forniti dal giudice dopo il
recupero del sensore eDNA), calcola la % di frequenza vista per ognuna
(`count_specie / totale * 100`) da mostrare a schermo per il giudice.

La funzione `frequency()` è pura e testabile; importare questo modulo non ha
side-effect. La demo CLI è sotto `if __name__ == "__main__"`.
"""


def frequency(counts):
    """Calcola la frequenza percentuale di ciascuna specie.

    Args:
        counts: dict {species_name: int} oppure list[{"name": str, "count": int}].

    Returns:
        dict con keys:
          ok (bool), total (int), species (list di dict con name, count,
          percent [precisione piena], percent_display [arrotondato a 2 decimali]).
        In caso di totale <= 0: ok=False, error="empty_or_zero_total".
    """
    if isinstance(counts, dict):
        items = list(counts.items())
    else:
        items = [(d["name"], d["count"]) for d in counts]

    total = sum(int(c) for _, c in items)
    if total <= 0:
        return {"ok": False, "error": "empty_or_zero_total",
                "total": 0, "species": []}

    species = []
    for name, c in items:
        pct = int(c) / total * 100.0
        species.append({
            "name": name,
            "count": int(c),
            "percent": pct,                    # precisione piena
            "percent_display": round(pct, 2),  # per la GUI / il giudice
        })
    return {"ok": True, "total": total, "species": species}


# --- Colori ANSI (solo per l'output CLI) ---
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_CYAN  = "\033[36m"
_WHITE = "\033[97m"

# Le 10 specie del manuale, con i conteggi golden (totale = 84).
_SAMPLE_COUNTS = {
    "Snow crab": 19,
    "Acadian hermit crab": 3,
    "Western Atlantic Hairy Hermit Crab": 1,
    "European Green Crab": 9,
    "Rock Crab": 10,
    "Jonah Crab": 5,
    "Spiny Sunstar": 8,
    "Sea Urchin": 10,
    "Boreal Sea Star": 12,
    "Daisy brittle star": 7,
}


def _run_cli():
    res = frequency(_SAMPLE_COUNTS)

    print(f"\n{_BOLD}{_CYAN}{'═' * 56}{_RESET}")
    print(f"{_BOLD}{_CYAN}   🧬  eDNA Frequency Calculator{_RESET}")
    print(f"{_BOLD}{_CYAN}{'═' * 56}{_RESET}")
    print(f"  {_BOLD}{_WHITE}{'Species':<38}{'count':>6}{'%':>9}{_RESET}")
    print(f"  {'-' * 53}")
    for s in res["species"]:
        print(f"  {s['name']:<38}{s['count']:>6}{s['percent_display']:>8.2f}%")
    print(f"  {'-' * 53}")
    print(f"  {_BOLD}{_WHITE}{'TOTALE':<38}{res['total']:>6}"
          f"{100.00:>8.2f}%{_RESET}")
    print(f"{_BOLD}{_CYAN}{'═' * 56}{_RESET}\n")


if __name__ == "__main__":
    _run_cli()
