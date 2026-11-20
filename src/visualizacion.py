"""Dibujo del campus: enlaces candidatos, MST y (luego) enlaces críticos y propuestos."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLOR_NODO = {"centro_datos": "#c0392b", "hub": "#2c6fbb", "edificio": "#7f8c8d"}
TAM_NODO = {"centro_datos": 260, "hub": 170, "edificio": 110}
X_AVENIDA = 520


def dibujar_red(grafo, resaltar=None, criticos=None, propuestos=None,
                titulo="", archivo=None):
    """Dibuja el grafo sobre el plano del campus.

    resaltar:   aristas (u, v, ...) a pintar fuerte (p. ej., el MST)
    criticos:   aristas a pintar en rojo
    propuestos: aristas nuevas a pintar en verde punteado
    """
    fig, ax = plt.subplots(figsize=(12, 7.5))

    # Avenida interna
    ax.axvspan(X_AVENIDA - 6, X_AVENIDA + 6, color="#f5e6b8", zorder=0)
    ax.text(X_AVENIDA + 10, 595, "Avenida Interna", fontsize=8, color="#8a6d1f")

    def segmento(u, v, **estilo):
        (x1, y1), (x2, y2) = grafo.pos[u], grafo.pos[v]
        ax.plot([x1, x2], [y1, y2], **estilo)

    for u, v, _ in grafo.aristas():
        segmento(u, v, color="#d5d8dc", lw=1, zorder=1)
    for u, v, *_ in resaltar or []:
        segmento(u, v, color="#34495e", lw=2.6, zorder=2)
    for u, v, *_ in criticos or []:
        segmento(u, v, color="#e74c3c", lw=3.4, zorder=3)
    for u, v, *_ in propuestos or []:
        segmento(u, v, color="#27ae60", lw=2.6, ls="--", zorder=3)

    for v, (x, y) in grafo.pos.items():
        tipo = grafo.info[v].get("tipo", "edificio")
        ax.scatter(x, y, s=TAM_NODO[tipo], c=COLOR_NODO[tipo], zorder=4,
                   edgecolors="white", linewidths=1.5)
        ax.annotate(v, (x, y), xytext=(7, 7), textcoords="offset points",
                    fontsize=9, weight="bold", zorder=5)

    for tipo, color in COLOR_NODO.items():
        ax.scatter([], [], c=color, s=80, label=tipo.replace("_", " ").capitalize())
    ax.plot([], [], color="#d5d8dc", label="Enlace candidato")
    if resaltar:
        ax.plot([], [], color="#34495e", lw=2.6, label="Árbol de expansión mínima")
    if criticos:
        ax.plot([], [], color="#e74c3c", lw=3.4, label="Enlace crítico")
    if propuestos:
        ax.plot([], [], color="#27ae60", lw=2.6, ls="--", label="Enlace propuesto")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)

    ax.set_title(titulo)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.set_xlim(0, 840)
    ax.set_ylim(20, 620)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    if archivo:
        fig.savefig(archivo, dpi=150)
        plt.close(fig)
    return fig
