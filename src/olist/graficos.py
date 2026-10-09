"""Galeria de gráficos do projeto. Cada função consulta o banco, desenha e devolve a figura."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde

from .data import consulta
from .estilo import COR, SEQ, subtitulo, fonte
from .mapa import tile_map

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
CATEGORIA_PT = {"bed_bath_table": "cama, mesa e banho", "health_beauty": "saúde e beleza", "sports_leisure": "esporte e lazer",
                "computers_accessories": "informática", "furniture_decor": "móveis e decoração", "housewares": "utilidades domésticas",
                "watches_gifts": "relógios e presentes", "telephony": "telefonia", "auto": "automotivo", "toys": "brinquedos",
                "cool_stuff": "presentes criativos", "garden_tools": "jardinagem", "baby": "bebês", "perfumery": "perfumaria"}


def cat_pt(c):
    return CATEGORIA_PT.get(c, c.replace("_", " "))


REGIAO = {**dict.fromkeys(["SP", "RJ", "MG", "ES"], "Sudeste"), **dict.fromkeys(["PR", "SC", "RS"], "Sul"),
          **dict.fromkeys(["MT", "MS", "GO", "DF"], "Centro-Oeste"),
          **dict.fromkeys(["BA", "SE", "AL", "PE", "PB", "RN", "CE", "PI", "MA"], "Nordeste"),
          **dict.fromkeys(["PA", "AP", "AM", "RR", "RO", "AC", "TO"], "Norte")}


def br(v, casas=0):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _eixo_mes(ax, meses=(1, 4, 7, 10)):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=list(meses)))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(
        lambda v, _: f"{MESES[mdates.num2date(v).month - 1]}/{mdates.num2date(v):%y}"))


def pedidos_diarios():
    d = consulta("SELECT data_compra, COUNT(DISTINCT order_id) AS pedidos FROM fact_itens GROUP BY data_compra")
    d["data_compra"] = pd.to_datetime(d["data_compra"])
    return d.set_index("data_compra")["pedidos"].asfreq("D", fill_value=0)


# 1 -------------------------------------------------------------------------
def serie_semanal():
    s = pedidos_diarios().resample("W-SUN").sum()["2017-01-08":"2018-08-19"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(s.index, s.values, color=COR["principal"], lw=2)
    ax.fill_between(s.index, s.values, color=COR["principal"], alpha=0.07)
    bf = s["2017-11-19":"2017-11-26"].idxmax()
    ax.scatter([bf], [s[bf]], s=60, color=COR["destaque"], zorder=3, edgecolor="white", linewidth=1.5)
    ax.annotate(f"Black Friday 2017\n{br(s[bf])} pedidos na semana", (bf, s[bf]), xytext=(-150, -8),
                textcoords="offset points", fontsize=9, color=COR["texto"],
                arrowprops=dict(arrowstyle="-", color=COR["texto2"], lw=0.8))
    ax.axvspan(pd.Timestamp("2018-05-21"), pd.Timestamp("2018-06-01"), color=COR["destaque"], alpha=0.12, lw=0)
    ax.text(pd.Timestamp("2018-05-26"), s.max() * 0.82, "greve dos\ncaminhoneiros", ha="center",
            fontsize=8.5, color=COR["destaque"])
    ax.set_ylim(0, s.max() * 1.12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: br(v)))
    _eixo_mes(ax); ax.grid(axis="x", visible=False)
    ax.set_title("A demanda triplicou em 2017 e se estabilizou em 2018")
    subtitulo(ax, "Pedidos por semana, jan/2017 – ago/2018")
    fonte(fig)
    return fig


# 2 -------------------------------------------------------------------------
def mapa_prazo():
    p = consulta("""SELECT uf_cliente, AVG(dias_entrega) d FROM pedidos
                    WHERE order_status='delivered' AND dias_entrega IS NOT NULL GROUP BY uf_cliente""")
    fig, ax = plt.subplots(figsize=(5.6, 7))
    ax.grid(False)
    tile_map(ax, dict(zip(p.uf_cliente, p.d)), fmt="{:.0f} dias")
    ax.set_title("Quanto mais longe de SP, mais espera", pad=30)
    ax.text(0, 1.035, "Prazo médio de entrega por estado do cliente (dias)", transform=ax.transAxes,
            fontsize=10, color=COR["texto2"])
    fonte(fig)
    return fig


# 3 -------------------------------------------------------------------------
def dumbbell_prazo():
    p = consulta("""SELECT uf_cliente, AVG(dias_prometidos) prom, AVG(dias_entrega) real FROM pedidos
                    WHERE order_status='delivered' AND dias_entrega IS NOT NULL GROUP BY uf_cliente""")
    p = p.sort_values("real").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 8))
    y = np.arange(len(p))
    ax.hlines(y, p.real, p.prom, color=COR["contexto"], lw=2.5, zorder=1)
    ax.scatter(p.real, y, color=COR["principal"], s=55, zorder=2, label="Entrega real", edgecolor="white", linewidth=1.2)
    ax.scatter(p.prom, y, color=COR["destaque"], s=55, zorder=2, label="Prazo prometido", edgecolor="white", linewidth=1.2)
    ax.set_yticks(y, p.uf_cliente); ax.grid(axis="y", visible=False)
    ax.set_xlabel("dias desde a compra")
    i = (p.prom - p.real).idxmax(); r = p.loc[i]
    ax.annotate(f"{r.uf_cliente}: promete {r.prom:.0f}, entrega em {r.real:.0f}", (r.prom, i), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=8.5, color=COR["texto2"])
    ax.legend(loc="lower right", ncol=2)
    ax.set_title("A Olist prometia prazos muito maiores do que entregava")
    subtitulo(ax, f"Média por estado · folga média de {(p.prom - p.real).mean():.0f} dias entre o prometido e o real")
    fonte(fig)
    return fig


# 4 -------------------------------------------------------------------------
def atraso_nota():
    p = consulta("""SELECT dias_atraso, nota FROM pedidos WHERE order_status='delivered'
                    AND dias_atraso IS NOT NULL AND nota IS NOT NULL""")
    bins = [-1e9, -7, 0, 3, 7, 14, 1e9]
    lab = ["7+ dias\nadiantado", "até 7 dias\nadiantado", "1–3 dias\natrasado", "4–7 dias\natrasado",
           "8–14 dias\natrasado", "15+ dias\natrasado"]
    p["faixa"] = pd.cut(p.dias_atraso, bins, labels=lab)
    g = p.groupby("faixa", observed=True).agg(nota=("nota", "mean"), n=("nota", "size"))
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.set_axisbelow(True)
    ax.bar(range(len(g)), g.nota, color=[COR["principal"]] * 2 + [COR["destaque"]] * 4, width=0.62)
    for i, v in enumerate(g.nota):
        ax.text(i, v + 0.06, br(v, 1), ha="center", fontsize=10.5, fontweight="bold", color=COR["texto"])
    ax.set_xticks(range(len(g)), [f"{l}\nn = {br(n)}" for l, n in zip(g.index, g.n)])
    ax.set_ylim(0, 5.3); ax.grid(axis="x", visible=False); ax.set_ylabel("nota média (1 a 5)")
    ax.set_title("Um atraso derruba a avaliação; adiantar quase não muda nada")
    subtitulo(ax, "Nota média da avaliação por faixa de atraso em relação ao prazo prometido")
    fonte(fig, y=-0.09)
    return fig


# 5 -------------------------------------------------------------------------
def calendario():
    s = pedidos_diarios()["2017-01-01":"2018-08-31"]
    fig, axes = plt.subplots(2, 1, figsize=(11, 4.4), gridspec_kw={"hspace": 0.45})
    vmax = np.percentile(s, 99)
    for ax, ano in zip(axes, [2017, 2018]):
        x = s[str(ano)]
        semana = ((x.index - pd.Timestamp(f"{ano}-01-01")).days + pd.Timestamp(f"{ano}-01-01").weekday()) // 7
        m = np.full((7, 53), np.nan)
        m[x.index.weekday, semana] = x.values
        ax.imshow(m, aspect="equal", cmap=SEQ, vmin=0, vmax=vmax, interpolation="none")
        ax.set_yticks([0, 2, 4, 6], ["seg", "qua", "sex", "dom"], fontsize=8)
        inicio_mes = [((pd.Timestamp(f"{ano}-{mm:02d}-01") - pd.Timestamp(f"{ano}-01-01")).days
                       + pd.Timestamp(f"{ano}-01-01").weekday()) // 7 for mm in range(1, 13)]
        ax.set_xticks(inicio_mes, MESES, fontsize=8)
        ax.grid(False); ax.set_ylabel(str(ano), rotation=0, ha="right", va="center", fontsize=11,
                                      fontweight="bold", color=COR["texto"])
        for sp in ax.spines.values():
            sp.set_visible(False)
    axes[0].set_title("A Black Friday de 2017 foi o pico do período; sábado e domingo são os dias mais fracos")
    subtitulo(axes[0], "Pedidos por dia (cor mais escura = mais pedidos)")
    fonte(fig, y=0.0)
    return fig


# 6 -------------------------------------------------------------------------
def multiplos_categorias(n=8):
    d = consulta("SELECT data_compra, categoria, COUNT(DISTINCT order_id) p FROM fact_itens GROUP BY 1, 2")
    d["data_compra"] = pd.to_datetime(d["data_compra"])
    d = d[(d.data_compra >= "2017-01-01") & (d.data_compra <= "2018-08-31")]
    top = d.groupby("categoria").p.sum().nlargest(n).index
    piv = d.pivot_table(index="data_compra", columns="categoria", values="p", aggfunc="sum").fillna(0)
    piv = piv.resample("MS").sum()
    fig, axes = plt.subplots(2, 4, figsize=(12, 5.2), sharex=True, sharey=True)
    for ax, cat in zip(axes.flat, top):
        for outra in top:
            if outra != cat:
                ax.plot(piv.index, piv[outra], color=COR["contexto"], lw=0.8, alpha=0.6)
        ax.plot(piv.index, piv[cat], color=COR["principal"], lw=2)
        ax.set_title(cat_pt(cat), fontsize=10, pad=6)
        ax.grid(axis="x", visible=False)
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
        ax.xaxis.set_major_formatter(plt.FuncFormatter(
            lambda v, _: f"{MESES[mdates.num2date(v).month - 1]}/{mdates.num2date(v):%y}"))
        ax.tick_params(labelsize=8)
    fig.suptitle("Saúde e beleza cresceu sem parar; informática teve um pico e devolveu", x=0.01, ha="left",
                 fontsize=13.5, fontweight="bold", color=COR["texto"], y=1.02)
    fig.text(0.01, 0.955, "Pedidos por mês nas 8 maiores categorias (cada painel destaca uma; as demais em cinza)",
             fontsize=10, color=COR["texto2"])
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fonte(fig)
    return fig


# 7 -------------------------------------------------------------------------
def waterfall_receita(n=6):
    d = consulta("""SELECT categoria, substr(data_compra,1,4) ano, SUM(preco) r FROM fact_itens
                    WHERE substr(data_compra,6,2) BETWEEN '01' AND '06' AND substr(data_compra,1,4) IN ('2017','2018')
                    GROUP BY 1, 2""")
    piv = d.pivot(index="categoria", columns="ano", values="r").fillna(0) / 1e6
    delta = (piv["2018"] - piv["2017"]).sort_values(ascending=False)
    top = delta.head(n)
    resto = delta.drop(top.index).sum()
    passos = [("1º sem. 2017", piv["2017"].sum(), "total")] + \
             [(cat_pt(c), v, "delta") for c, v in top.items()] + \
             [("demais categorias", resto, "delta"), ("1º sem. 2018", piv["2018"].sum(), "total")]
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.set_axisbelow(True)
    acum = 0
    for i, (rot, v, tipo) in enumerate(passos):
        if tipo == "total":
            ax.bar(i, v, color=COR["texto2"], width=0.62); topo = v; acum = v
        else:
            ax.bar(i, v, bottom=acum, color=COR["principal"] if v >= 0 else COR["destaque"], width=0.62)
            acum += v; topo = acum if v >= 0 else acum - v
        ax.text(i, topo + 0.05, ("+" if tipo == "delta" and v > 0 else "") + br(v, 1), ha="center",
                fontsize=9, color=COR["texto"], fontweight="bold")
    ax.set_xticks(range(len(passos)), [p[0] for p in passos], rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("receita de itens (R$ milhões)"); ax.grid(axis="x", visible=False)
    ax.set_title("Seis categorias explicam metade do crescimento da receita")
    subtitulo(ax, "Receita de itens no 1º semestre, 2017 → 2018 (R$ milhões), por categoria")
    fonte(fig, y=-0.17)
    return fig


# 8 -------------------------------------------------------------------------
def funil():
    p = consulta("""SELECT
        COUNT(*) feitos,
        SUM(order_status NOT IN ('canceled','unavailable','created')) aprovados,
        SUM(order_status IN ('shipped','delivered')) enviados,
        SUM(order_status = 'delivered') entregues,
        SUM(order_status = 'delivered' AND dias_atraso <= 0) no_prazo,
        SUM(order_status = 'delivered' AND dias_atraso <= 0 AND nota = 5) nota5
        FROM pedidos""").iloc[0]
    etapas = [("Pedidos feitos", p.feitos), ("Aprovados", p.aprovados), ("Enviados", p.enviados),
              ("Entregues", p.entregues), ("Entregues no prazo", p.no_prazo), ("…e avaliados com nota 5", p.nota5)]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    mx = etapas[0][1]
    for i, (rot, v) in enumerate(etapas):
        w = v / mx
        cor = COR["destaque"] if i == len(etapas) - 1 else COR["principal"]
        ax.barh(i, w, left=(1 - w) / 2, color=cor, height=0.72)
        ax.text(0.5, i, f"{rot}: {br(v)}  ({br(100 * v / mx)}%)", ha="center", va="center",
                fontsize=9.5, color="white", fontweight="bold")
    ax.invert_yaxis(); ax.axis("off")
    ax.set_title("97% dos pedidos chegam, mas só 55% chegam no prazo e com nota 5")
    subtitulo(ax, "Funil de pedidos, set/2016 – out/2018")
    fonte(fig)
    return fig


# 9 -------------------------------------------------------------------------
def distribuicao_frete():
    d = consulta("SELECT uf_cliente, preco, frete FROM fact_itens WHERE preco > 0")
    d["regiao"] = d.uf_cliente.map(REGIAO)
    d["pct"] = 100 * d.frete / d.preco
    ordem = d.groupby("regiao").pct.median().sort_values().index
    xs = np.linspace(0, 120, 400)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, reg in enumerate(ordem):
        v = d.loc[d.regiao == reg, "pct"].clip(upper=120)
        dens = gaussian_kde(v.sample(min(len(v), 20000), random_state=0))(xs)
        dens = dens / dens.max() * 0.9
        base = i
        cor = COR["destaque"] if reg == "Norte" else COR["principal"]
        ax.fill_between(xs, base, base + dens, color=cor, alpha=0.85, lw=0, zorder=10 - i)
        ax.plot(xs, base + dens, color="white", lw=1, zorder=10 - i)
        med = v.median()
        ax.text(121, base + 0.15, f"mediana {br(med)}%", fontsize=8.5, color=COR["texto2"], va="bottom")
    ax.set_yticks(np.arange(len(ordem)) + 0.3, ordem); ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 140); ax.set_xlabel("frete como % do preço do item")
    ax.set_title("No Norte, o frete pesa quase o dobro do que no Sudeste")
    subtitulo(ax, "Distribuição do frete em relação ao preço do item, por região do cliente")
    fonte(fig)
    return fig


# 10 ------------------------------------------------------------------------
def slope_regioes():
    d = consulta("""SELECT uf_cliente, substr(data_compra,1,4) ano, COUNT(DISTINCT order_id) p FROM fact_itens
                    WHERE substr(data_compra,6,2) BETWEEN '01' AND '08' AND substr(data_compra,1,4) IN ('2017','2018')
                    GROUP BY 1, 2""")
    d["regiao"] = d.uf_cliente.map(REGIAO)
    g = d.groupby(["regiao", "ano"]).p.sum().unstack()
    g = g.div(g.sum()) * 100
    fig, ax = plt.subplots(figsize=(6, 4.6))
    for reg, r in g.iterrows():
        cor = COR["principal"] if reg != "Sudeste" else COR["destaque"]
        ax.plot([0, 1], [r["2017"], r["2018"]], color=cor, lw=2, marker="o", ms=7, markeredgecolor="white")
        ax.text(-0.04, r["2017"], f"{reg} {br(r['2017'], 1)}%", ha="right", va="center", fontsize=9)
        ax.text(1.04, r["2018"], f"{br(r['2018'], 1)}%", ha="left", va="center", fontsize=9)
    ax.set_xlim(-0.6, 1.3); ax.set_xticks([0, 1], ["jan–ago 2017", "jan–ago 2018"])
    ax.set_yticks([]); ax.grid(False)
    ax.set_title("O Sudeste ganhou 3 pontos; as demais regiões perderam")
    subtitulo(ax, "% dos pedidos por região do cliente")
    fonte(fig)
    return fig


# 11 ------------------------------------------------------------------------
def heatmap_hora():
    d = consulta("""SELECT CAST(strftime('%w', ts_compra) AS INT) dow, CAST(strftime('%H', ts_compra) AS INT) h,
                    COUNT(DISTINCT order_id) p FROM fact_itens GROUP BY 1, 2""")
    m = d.pivot(index="dow", columns="h", values="p").reindex(index=[1, 2, 3, 4, 5, 6, 0]).fillna(0)
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.imshow(m.values, cmap=SEQ, aspect="auto", interpolation="none")
    ax.set_yticks(range(7), ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"])
    ax.set_xticks(range(0, 24, 2), [f"{h}h" for h in range(0, 24, 2)])
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("82% dos pedidos acontecem entre 10h e 22h; sábado é o dia mais fraco")
    subtitulo(ax, "Pedidos por dia da semana e hora da compra (cor mais escura = mais pedidos)")
    fonte(fig)
    return fig


GALERIA = [serie_semanal, mapa_prazo, dumbbell_prazo, atraso_nota, calendario, multiplos_categorias,
           waterfall_receita, funil, distribuicao_frete, slope_regioes, heatmap_hora]


# ---------------------------------------------------------------------------
# Previsão
# ---------------------------------------------------------------------------
def backtest_modelos(ws: pd.DataFrame):
    """ws: WAPE semanal por modelo e corte (horizonte de 4 semanas)."""
    media = ws.groupby("modelo").wape.mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    for i, m in enumerate(media.index):
        pts = ws[ws.modelo == m].wape * 100
        ax.scatter(pts, np.full(len(pts), i), color=COR["contexto"], s=26, zorder=2)
        cor = COR["principal"] if i == len(media) - 1 else COR["texto2"]
        ax.scatter(media[m] * 100, i, color=cor, s=90, zorder=3, edgecolor="white", linewidth=1.5)
        ax.text(media[m] * 100, i - 0.32, f"{br(media[m] * 100, 1)}%", ha="center", va="top", fontsize=9, color=COR["texto"])
    ax.set_yticks(range(len(media)), media.index); ax.grid(axis="y", visible=False)
    ax.set_ylim(-0.8, len(media) - 0.5)
    ax.set_xlabel("erro semanal (WAPE, %) — cinza: cada corte; ponto maior: média")
    ax.set_title("Nenhum modelo supera de verdade o ingênuo a 4 semanas")
    subtitulo(ax, "Backtest com 8 cortes em 2018, previsão de 28 dias somada por semana")
    fonte(fig)
    return fig


def cadencia(erro_4s: float, erro_1s: float):
    fig, ax = plt.subplots(figsize=(8, 2.8))
    vals = [erro_4s * 100, erro_1s * 100]
    rot = ["Prever 4 semanas à frente\n(melhor modelo)", "Replanejar toda semana\n(repetir a última semana)"]
    ax.set_axisbelow(True)
    ax.barh([1, 0], vals, color=[COR["contexto"], COR["principal"]], height=0.55)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: br(v)))
    for y_, v in zip([1, 0], vals):
        ax.text(v + 0.3, y_, f"{br(v, 1)}%", va="center", fontsize=11, fontweight="bold", color=COR["texto"])
    ax.set_yticks([1, 0], rot); ax.set_xlim(0, max(vals) * 1.25); ax.grid(axis="y", visible=False)
    ax.set_xlabel("erro da demanda semanal (WAPE, %)")
    ax.set_title("Replanejar toda semana erra um terço menos do que um modelo melhor")
    subtitulo(ax, "Backtest em 2018 · erro médio na previsão do total de pedidos da semana")
    fonte(fig, y=-0.12)
    return fig


def previsto_real(err7: pd.DataFrame, modelo="Sazonal ingênuo"):
    e = err7[err7.modelo == modelo].groupby("corte")[["real", "prev"]].sum()
    e.index = pd.to_datetime(e.index) + pd.Timedelta(days=1)  # início da semana prevista
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(e.index, e.real, color=COR["texto"], lw=2, label="Real")
    ax.plot(e.index, e.prev, color=COR["principal"], lw=2, ls="--", label="Previsto (semana anterior)")
    ax.fill_between(e.index, e.real, e.prev, color=COR["destaque"], alpha=0.12, lw=0)
    ax.annotate("greve dos caminhoneiros:\nnenhuma previsão antecipava", (pd.Timestamp("2018-05-21"), e.real.loc["2018-05-21"]),
                xytext=(-170, -5), textcoords="offset points", fontsize=8.5, color=COR["destaque"],
                arrowprops=dict(arrowstyle="-", color=COR["destaque"], lw=0.8))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: br(v)))
    _eixo_mes(ax, meses=range(1, 13)); ax.grid(axis="x", visible=False); ax.legend(loc="upper left")
    ax.set_ylim(800, e[["real", "prev"]].max().max() * 1.08)
    ax.set_title("Repetir a última semana acompanha bem, mas não antecipa choques")
    subtitulo(ax, "Pedidos por semana em 2018 · previsão = total da semana anterior, feita no domingo")
    fonte(fig)
    return fig
