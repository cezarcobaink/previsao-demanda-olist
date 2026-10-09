"""Previsão de pedidos diários com backtesting em janelas móveis (rolling origin).

Regras para não vazar informação do futuro:
- cada modelo só enxerga dados até a data de corte;
- as variáveis usadas no horizonte são todas conhecidas no corte (calendário e nível recente).
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor
from sklearn.ensemble import HistGradientBoostingRegressor

HORIZONTE = 28
DATAS_ESPECIAIS = {  # eventos conhecidos com antecedência
    "black_friday": ["2017-11-24", "2018-11-23"],
}


def calendario(idx: pd.DatetimeIndex, inicio: pd.Timestamp) -> pd.DataFrame:
    X = pd.DataFrame(index=idx)
    X["t"] = (idx - inicio).days / 365.0
    for d in range(7):
        X[f"dow_{d}"] = (idx.weekday == d).astype(float)
    for m in range(1, 13):
        X[f"mes_{m}"] = (idx.month == m).astype(float)
    bf = pd.to_datetime(DATAS_ESPECIAIS["black_friday"])
    dist = np.min(np.abs((idx.values[:, None] - bf.values[None, :]).astype("timedelta64[D]").astype(int)), axis=1)
    X["semana_bf"] = (dist <= 3).astype(float)
    X["dia_bf"] = (dist == 0).astype(float)
    return X


def _nivel(y_hist: pd.Series) -> float:
    return float(y_hist.iloc[-28:].mean())


def prever(nome: str, y_hist: pd.Series, datas: pd.DatetimeIndex) -> np.ndarray:
    if nome == "Sazonal ingênuo":           # repete a última semana
        ult = y_hist.iloc[-7:]
        return np.array([ult[ult.index.weekday == d.weekday()].iloc[0] for d in datas], dtype=float)
    if nome == "Média sazonal (4 semanas)":  # média das 4 últimas ocorrências do dia da semana
        h = y_hist.iloc[-28:]
        return np.array([h[h.index.weekday == d.weekday()].mean() for d in datas], dtype=float)
    inicio = y_hist.index[0]
    Xh, Xf = calendario(y_hist.index, inicio), calendario(datas, inicio)
    if nome == "Regressão de Poisson":
        # sem tendência explícita (extrapolar tendência explode); o nível recente entra como log
        nivel_h = y_hist.shift(1).rolling(28, min_periods=7).mean().bfill()
        cols = [c for c in Xh.columns if c.startswith("dow_") or c in ("semana_bf", "dia_bf")]
        Xh2 = Xh[cols].assign(log_nivel=np.log(nivel_h.values))
        Xf2 = Xf[cols].assign(log_nivel=np.log(_nivel(y_hist)))
        m = PoissonRegressor(alpha=1e-4, max_iter=3000).fit(Xh2, y_hist.values)
        return m.predict(Xf2)
    if nome == "Gradient boosting":
        # nível recente como variável: no histórico, média móvel de 28 dias defasada; no futuro, o nível no corte
        nivel_h = y_hist.shift(1).rolling(28, min_periods=7).mean().bfill()
        Xh = Xh.assign(nivel=nivel_h.values, dow=y_hist.index.weekday)
        Xf = Xf.assign(nivel=_nivel(y_hist), dow=datas.weekday)
        m = HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05,
                                          min_samples_leaf=20, random_state=0).fit(Xh, y_hist.values)
        return m.predict(Xf)
    if nome == "Combinação (média dos 3)":
        return np.mean([prever(n, y_hist, datas) for n in
                        ("Média sazonal (4 semanas)", "Regressão de Poisson", "Gradient boosting")], axis=0)
    raise ValueError(nome)


MODELOS = ["Sazonal ingênuo", "Média sazonal (4 semanas)", "Regressão de Poisson", "Gradient boosting", "Combinação (média dos 3)"]


def wape(real, prev):
    real, prev = np.asarray(real, float), np.asarray(prev, float)
    return np.abs(real - prev).sum() / real.sum()


def backtest(y: pd.Series, cortes, inicio_treino="2017-01-01", horizonte=HORIZONTE):
    linhas, erros = [], []
    for c in pd.to_datetime(cortes):
        hist = y[inicio_treino:c]
        datas = pd.date_range(c + pd.Timedelta(days=1), periods=horizonte, freq="D")
        real = y.reindex(datas)
        for nome in MODELOS:
            p = prever(nome, hist, datas)
            linhas.append({"corte": c.date(), "modelo": nome, "wape": wape(real, p)})
            erros.append(pd.DataFrame({"modelo": nome, "corte": c, "h": np.arange(1, horizonte + 1),
                                       "data": datas, "real": real.values, "prev": p}))
    return pd.DataFrame(linhas), pd.concat(erros, ignore_index=True)


def quantil_newsvendor(custo_falta: float, custo_sobra: float) -> float:
    """Quantil ótimo da demanda a planejar: custo de faltar / (custo de faltar + custo de sobrar)."""
    return custo_falta / (custo_falta + custo_sobra)


def wape_semanal(err: pd.DataFrame) -> pd.DataFrame:
    """WAPE somando a demanda por semana do horizonte (o que importa para planejar capacidade)."""
    e = err.assign(semana=(err.h - 1) // 7)
    g = e.groupby(["modelo", "corte", "semana"])[["real", "prev"]].sum().reset_index()
    return g.groupby(["modelo", "corte"]).apply(lambda d: wape(d.real, d.prev), include_groups=False).rename("wape").reset_index()


def planejamento(err: pd.DataFrame, modelo: str, custo_falta=3.0, custo_sobra=1.0):
    """Compara planejar capacidade semanal no ponto previsto versus no quantil ótimo.

    O quantil vem só dos cortes ANTERIORES (sem olhar o futuro); o primeiro corte usa o ponto previsto.
    """
    q = quantil_newsvendor(custo_falta, custo_sobra)
    e = err[err.modelo == modelo].assign(semana=lambda d: (d.h - 1) // 7)
    sem = e.groupby(["corte", "semana"])[["real", "prev"]].sum().reset_index()
    sem["razao"] = sem.real / sem.prev
    linhas = []
    for c in sorted(sem.corte.unique()):
        atual = sem[sem.corte == c]
        passado = sem[sem.corte < c]
        mult = np.quantile(passado.razao, q) if len(passado) >= 4 else 1.0
        for estrategia, cap in [("Planejar no ponto previsto", atual.prev), (f"Planejar no quantil {q:.0%}", atual.prev * mult)]:
            falta = np.clip(atual.real - cap, 0, None).sum()
            sobra = np.clip(cap - atual.real, 0, None).sum()
            linhas.append({"corte": c, "estrategia": estrategia, "falta": falta, "sobra": sobra,
                           "custo": custo_falta * falta + custo_sobra * sobra, "mult": mult})
    return pd.DataFrame(linhas)
