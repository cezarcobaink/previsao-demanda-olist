"""Mapa em grade de quadrados (tile grid) dos estados brasileiros: compara estados sem a distorção de área."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from .estilo import COR, SEQ

GRADE = {
    "RR": (1, 0), "AP": (3, 0),
    "AM": (1, 1), "PA": (2, 1), "MA": (3, 1), "CE": (4, 1), "RN": (5, 1),
    "AC": (0, 2), "RO": (1, 2), "TO": (2, 2), "PI": (3, 2), "PE": (4, 2), "PB": (5, 2),
    "MT": (1, 3), "GO": (2, 3), "DF": (3, 3), "BA": (4, 3), "AL": (5, 3),
    "MS": (1, 4), "SP": (2, 4), "MG": (3, 4), "ES": (4, 4), "SE": (5, 4),
    "PR": (2, 5), "RJ": (3, 5),
    "SC": (2, 6),
    "RS": (2, 7),
}


def tile_map(ax, valores, fmt="{:.0f}", vmin=None, vmax=None, cmap=SEQ):
    vmin = min(valores.values()) if vmin is None else vmin
    vmax = max(valores.values()) if vmax is None else vmax
    for uf, (x, y) in GRADE.items():
        v = valores.get(uf)
        t = 0 if v is None else (v - vmin) / (vmax - vmin)
        cor = "#EEEEEE" if v is None else cmap(t)
        ax.add_patch(FancyBboxPatch((x + 0.04, -y + 0.04), 0.92, 0.92, boxstyle="round,pad=0,rounding_size=0.08",
                                    facecolor=cor, edgecolor="white", linewidth=1.5))
        claro = t > 0.38
        ax.text(x + 0.5, -y + 0.62, uf, ha="center", va="center", fontsize=10, fontweight="bold",
                color="white" if claro else COR["texto"])
        if v is not None:
            ax.text(x + 0.5, -y + 0.32, fmt.format(v), ha="center", va="center", fontsize=8.5,
                    color="white" if claro else COR["texto2"])
    ax.set_xlim(-0.1, 6.1); ax.set_ylim(-7.1, 1.1); ax.set_aspect("equal"); ax.axis("off")
