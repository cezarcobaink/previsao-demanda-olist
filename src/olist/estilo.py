"""Padrão visual único para todos os gráficos do projeto."""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

COR = {
    "principal": "#00806B",   # série principal (validada: croma, contraste e daltonismo)
    "destaque": "#C9721F",    # anomalia / ponto de atenção
    "contexto": "#B9C3BF",    # séries de contexto
    "texto": "#16211F",
    "texto2": "#56635F",
    "grade": "#E6EBE8",
    "fundo": "#FFFFFF",
}
SEQ = LinearSegmentedColormap.from_list("seq", ["#E3F1EC", "#7CC0AE", "#00806B", "#0A3F36"])


def aplicar():
    mpl.rcParams.update({
        "figure.facecolor": COR["fundo"], "axes.facecolor": COR["fundo"],
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.edgecolor": COR["grade"], "axes.labelcolor": COR["texto2"],
        "axes.titlesize": 13.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlecolor": COR["texto"], "axes.titlepad": 26,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.grid": True, "grid.color": COR["grade"], "grid.linewidth": 0.8,
        "xtick.color": COR["texto2"], "ytick.color": COR["texto2"],
        "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "savefig.dpi": 160, "savefig.bbox": "tight",
    })


def subtitulo(ax, texto):
    ax.text(0, 1.02, texto, transform=ax.transAxes, fontsize=10, color=COR["texto2"], va="bottom")


def fonte(fig, texto="Fonte: Olist Brazilian E-Commerce Public Dataset (2016–2018) · elaboração: Cézar Bento", y=-0.02):
    fig.text(0.01, y, texto, fontsize=8, color=COR["texto2"], ha="left", va="top")
