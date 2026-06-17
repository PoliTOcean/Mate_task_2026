"""Test per Task 2.5 — eDNA Frequency Calculator.

Eseguibili con `pytest` oppure direttamente con `python test_edna.py`
(non richiede dipendenze esterne).
"""

import edna

# Golden sample dal manuale: totale atteso 84.
GOLDEN = {
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


def _pct(result, name):
    return next(s for s in result["species"] if s["name"] == name)["percent"]


def test_golden_total_is_84():
    res = edna.frequency(GOLDEN)
    assert res["ok"] is True
    assert res["total"] == 84


def test_golden_known_percentages():
    res = edna.frequency(GOLDEN)
    assert abs(_pct(res, "Snow crab") - 22.619047619) < 1e-6
    assert abs(_pct(res, "Rock Crab") - 11.904761905) < 1e-6


def test_golden_percentages_sum_to_100():
    res = edna.frequency(GOLDEN)
    total_pct = sum(s["percent"] for s in res["species"])
    assert abs(total_pct - 100.0) < 1e-6


def test_golden_has_exactly_ten_species():
    res = edna.frequency(GOLDEN)
    assert len(res["species"]) == 10


def test_accepts_list_of_dicts():
    as_list = [{"name": n, "count": c} for n, c in GOLDEN.items()]
    res = edna.frequency(as_list)
    assert res["total"] == 84
    assert abs(_pct(res, "Snow crab") - 22.619047619) < 1e-6


def test_percent_display_is_rounded_to_two_decimals():
    res = edna.frequency(GOLDEN)
    snow = next(s for s in res["species"] if s["name"] == "Snow crab")
    assert snow["percent_display"] == 22.62


def test_zero_total_returns_error():
    res = edna.frequency({"a": 0, "b": 0})
    assert res["ok"] is False
    assert res["error"] == "empty_or_zero_total"
    assert res["total"] == 0
    assert res["species"] == []


def test_empty_input_returns_error():
    res = edna.frequency({})
    assert res["ok"] is False
    assert res["error"] == "empty_or_zero_total"


if __name__ == "__main__":
    import sys
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} test passati")
    sys.exit(1 if failed else 0)
