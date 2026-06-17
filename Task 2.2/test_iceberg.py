"""Test per Task 2.2 — Iceberg Threat Level.

Eseguibili con `pytest` oppure direttamente con `python test_iceberg.py`
(non richiede dipendenze esterne).
"""

import iceberg as ib


def _platform(result, name):
    return next(p for p in result["platforms"] if p["name"] == name)


def test_cpa_east_hits_terra_nova():
    # Iceberg sulla stessa latitudine di Terra Nova, in moto verso Est:
    # gli passa esattamente sopra -> CPA ~ 0 NM -> surface red.
    res = ib.evaluate(46.4, -48.5, 90.0, 95.0)
    tn = _platform(res, "Terra Nova")
    assert tn["passing_distance_nm"] == 0.0
    assert tn["surface_threat"] == "red"
    # keel_ratio = 95/91 ~ 1.044 (0.90 <= r < 1.10) -> subsea red.
    assert abs(tn["keel_ratio"] - 1.044) < 1e-3
    assert tn["subsea_threat"] == "red"


def test_cpa_north_is_about_4_14_nm():
    # Stesso punto, heading Nord: la CPA a Terra Nova e' ~4.14 NM.
    res = ib.evaluate(46.4, -48.5, 0.0, 95.0)
    tn = _platform(res, "Terra Nova")
    assert abs(tn["passing_distance_nm"] - 4.14) < 0.01
    assert tn["surface_threat"] == "red"   # < 5 NM


def test_keel_ratio_over_110_is_always_green():
    # keel 110 vs depth 91 -> ratio ~1.209 >= 1.10: l'iceberg si arena prima,
    # quindi sia surface sia subsea sono green anche con CPA = 0.
    res = ib.evaluate(46.4, -48.5, 90.0, 110.0)
    tn = _platform(res, "Terra Nova")
    assert tn["passing_distance_nm"] == 0.0
    assert tn["surface_threat"] == "green"
    assert tn["subsea_threat"] == "green"


def test_surface_threat_bands():
    assert ib._surface_threat(0.0, 1.0) == "red"      # < 5
    assert ib._surface_threat(4.99, 1.0) == "red"
    assert ib._surface_threat(5.0, 1.0) == "yellow"   # 5..10
    assert ib._surface_threat(10.0, 1.0) == "yellow"
    assert ib._surface_threat(10.01, 1.0) == "green"  # > 10
    assert ib._surface_threat(0.0, 1.10) == "green"   # 110% -> green


def test_subsea_threat_boundaries():
    # Dentro i 25 NM, classificazione per keel_ratio sui confini.
    assert ib._subsea_threat(0.0, 0.69) == "green"
    assert ib._subsea_threat(0.0, 0.70) == "yellow"
    assert ib._subsea_threat(0.0, 0.89) == "yellow"
    assert ib._subsea_threat(0.0, 0.90) == "red"
    assert ib._subsea_threat(0.0, 1.09) == "red"
    assert ib._subsea_threat(0.0, 1.10) == "green"
    # Oltre i 25 NM -> sempre green, qualunque sia il ratio.
    assert ib._subsea_threat(25.01, 0.95) == "green"


def test_evaluate_returns_all_four_platforms():
    res = ib.evaluate(46.0, -48.5, 45.0, 90.0)
    assert res["ok"] is True
    names = [p["name"] for p in res["platforms"]]
    assert names == ["Hibernia", "Sea Rose", "Terra Nova", "Hebron"]


def test_negative_keel_is_treated_as_positive():
    # Il manuale fornisce le profondita' come negative: abs() le normalizza.
    pos = ib.evaluate(46.4, -48.5, 90.0, 95.0)
    neg = ib.evaluate(46.4, -48.5, 90.0, -95.0)
    assert pos["platforms"] == neg["platforms"]


def test_forward_only_treats_behind_platform_as_current_distance():
    # Iceberg che si muove verso Nord (heading 0) ma con una piattaforma a Sud
    # (dietro). Con forward_only la distanza e' quella corrente, non la
    # perpendicolare alla retta infinita.
    perp = ib._passing_distance_nm(46.4, -48.4, 0.0, 46.3, -48.4)
    fwd = ib._passing_distance_nm(46.4, -48.4, 0.0, 46.3, -48.4,
                                  forward_only=True)
    assert perp == 0.0          # retta infinita: la piattaforma e' sulla linea
    assert fwd > 0.0            # semiretta in avanti: usa la distanza corrente


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
