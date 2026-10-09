import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from olist.previsao import MODELOS, backtest, prever, quantil_newsvendor, wape  # noqa: E402


def serie(n=500, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2017-01-01", periods=n, freq="D")
    base = 100 + 20 * (idx.weekday < 5)
    return pd.Series(rng.poisson(base), index=idx, dtype=float)


def test_wape_perfeito_e_conhecido():
    assert wape([10, 20], [10, 20]) == 0
    assert np.isclose(wape([10, 10], [5, 15]), 0.5)


def test_quantil_newsvendor():
    assert np.isclose(quantil_newsvendor(3, 1), 0.75)
    assert np.isclose(quantil_newsvendor(1, 1), 0.5)


def test_sem_vazamento_do_futuro():
    """Alterar os dados DEPOIS do corte não pode mudar a previsão."""
    y = serie()
    corte = y.index[400]
    datas = pd.date_range(corte + pd.Timedelta(days=1), periods=28, freq="D")
    y2 = y.copy()
    y2[y2.index > corte] *= 10
    for m in MODELOS:
        a = prever(m, y[:corte], datas)
        b = prever(m, y2[:corte], datas)
        assert np.allclose(a, b), m


def test_backtest_formato():
    y = serie()
    res, err = backtest(y, [y.index[380], y.index[420]], horizonte=14)
    assert set(res.modelo) == set(MODELOS)
    assert len(err) == 2 * len(MODELOS) * 14
    assert (res.wape >= 0).all()
