"""Pruebas de MST. Ejecutar desde la raíz:  python -m pytest"""

import networkx as nx
import pytest

from src.datos import cargar_campus
from src.grafo import Grafo, es_conexo
from src.mst import prim, kruskal


def a_networkx(grafo):
    G = nx.Graph()
    for u, v, peso in grafo.aristas():
        G.add_edge(u, v, weight=peso)
    return G


@pytest.fixture
def campus():
    return cargar_campus()


def test_dataset_conexo(campus):
    assert es_conexo(campus)


def test_prim_y_kruskal_mismo_costo(campus):
    costo_p = sum(p for *_, p in prim(campus)[0])
    costo_k = sum(p for *_, p in kruskal(campus)[0])
    assert costo_p == costo_k


def test_costo_igual_a_networkx(campus):
    esperado = nx.minimum_spanning_tree(a_networkx(campus)).size(weight="weight")
    assert sum(p for *_, p in kruskal(campus)[0]) == esperado


def test_mst_tiene_n_menos_1_aristas_y_es_arbol(campus):
    arbol, _ = prim(campus)
    assert len(arbol) == len(campus.ady) - 1
    assert es_conexo(campus.subgrafo_con_aristas(arbol))


def test_grafo_desconectado_lanza_error():
    g = Grafo()
    for v in "ABC":
        g.agregar_vertice(v)
    g.agregar_arista("A", "B", 1)
    with pytest.raises(ValueError):
        kruskal(g)
