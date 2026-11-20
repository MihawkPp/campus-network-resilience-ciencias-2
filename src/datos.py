"""Carga del dataset del campus desde los CSV de data/."""

import csv
from pathlib import Path

from .grafo import Grafo

DIR_DATOS = Path(__file__).resolve().parent.parent / "data"


def _leer(nombre):
    with open(DIR_DATOS / nombre, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cargar_nodos():
    return _leer("nodos.csv")


def cargar_pares_criticos():
    """Lista de dicts: origen, destino, demanda_gbps (float), prioridad, justificacion."""
    pares = _leer("pares_criticos.csv")
    for p in pares:
        p["demanda_gbps"] = float(p["demanda_gbps"])
    return pares


def cargar_campus():
    """Grafo con todos los enlaces candidatos.

    peso      = costo_total_usd   (lo que minimiza el MST)
    capacidad = capacidad_gbps    (lo que usa el flujo máximo)
    """
    g = Grafo()
    for n in cargar_nodos():
        g.agregar_vertice(
            n["id"],
            pos=(float(n["x_m"]), float(n["y_m"])),
            nombre=n["nombre"],
            tipo=n["tipo"],
            demanda_gbps=float(n["demanda_gbps"]),
            critico=n["critico"] == "si",
        )
    for e in _leer("enlaces_candidatos.csv"):
        g.agregar_arista(
            e["origen"], e["destino"],
            peso=int(e["costo_total_usd"]),
            capacidad=float(e["capacidad_gbps"]),
        )
    return g
