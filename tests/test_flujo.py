"""Tests del algoritmo de flujo máximo (Edmonds-Karp) y corte mínimo.

Verificaciones:
  1. Grafo pequeño con resultado conocido manualmente.
  2. Teorema max-flow/min-cut: valor_flujo == capacidad_corte.
  3. Comparación contra networkx para el grafo del campus.
  4. Casos límite: sin ruta, mismos nodos, nodo inexistente.
  5. Verificación de que el grafo original no es modificado.

Ejecutar:  python -m pytest tests/
"""

import pytest
import networkx as nx

from src.grafo import Grafo
from src.datos import cargar_campus, cargar_pares_criticos
from src.flujo import flujo_maximo, corte_minimo


# ---------------------------------------------------------------------------
# Fixture: grafo pequeño con resultado conocido
# ---------------------------------------------------------------------------

@pytest.fixture
def grafo_pequeno():
    """Grafo de 4 nodos, 5 aristas — resultado calculable a mano.

        S --10-- A --10-- T
        |                |
        10               |
        |                |
        B ------10------ T
        S -- 5 -- B

    Capacidades:
      S-A = 10, S-B = 5 (pero también S-B directo no existe, ver abajo)
      A-T = 10, B-T = 10
      A-B = 1

    Grafo real de 4 nodos:
      S-A: 10, S-B: 10, A-T: 10, B-T: 10, A-B: 1

    Flujo máximo S→T = 20 (S→A→T: 10 + S→B→T: 10)
    """
    g = Grafo()
    for v in ("S", "A", "B", "T"):
        g.agregar_vertice(v)
    g.agregar_arista("S", "A", peso=1, capacidad=10)
    g.agregar_arista("S", "B", peso=1, capacidad=10)
    g.agregar_arista("A", "T", peso=1, capacidad=10)
    g.agregar_arista("B", "T", peso=1, capacidad=10)
    g.agregar_arista("A", "B", peso=1, capacidad=1)
    return g


@pytest.fixture
def grafo_cuello_botella():
    """Grafo con cuello de botella central.

      S --100-- M --1-- T

    Flujo máximo S→T = 1 (limitado por la arista M--T).
    """
    g = Grafo()
    for v in ("S", "M", "T"):
        g.agregar_vertice(v)
    g.agregar_arista("S", "M", peso=1, capacidad=100)
    g.agregar_arista("M", "T", peso=1, capacidad=1)
    return g


@pytest.fixture
def campus():
    return cargar_campus()


# ---------------------------------------------------------------------------
# Tests básicos con grafo pequeño
# ---------------------------------------------------------------------------

def test_flujo_maximo_grafo_pequeno(grafo_pequeno):
    """El flujo máximo S→T debe ser 20 Gbps."""
    valor, _ = flujo_maximo(grafo_pequeno, "S", "T")
    assert abs(valor - 20.0) < 1e-6


def test_flujo_cuello_botella(grafo_cuello_botella):
    """El cuello de botella limita el flujo a 1 Gbps."""
    valor, _ = flujo_maximo(grafo_cuello_botella, "S", "T")
    assert abs(valor - 1.0) < 1e-6


def test_max_flow_min_cut_teorema(grafo_pequeno):
    """Teorema Max-Flow/Min-Cut: valor_flujo == capacidad_corte."""
    valor_flujo, _ = flujo_maximo(grafo_pequeno, "S", "T")
    valor_corte, lado_s, aristas_corte = corte_minimo(grafo_pequeno, "S", "T")
    assert abs(valor_flujo - valor_corte) < 1e-6


def test_corte_minimo_separa_s_y_t(grafo_pequeno):
    """El lado S del corte debe contener S, el lado T debe contener T."""
    _, lado_s, _ = corte_minimo(grafo_pequeno, "S", "T")
    lado_t = {v for v in grafo_pequeno.ady if v not in lado_s}
    assert "S" in lado_s
    assert "T" in lado_t


def test_corte_minimo_aristas_cruzan_particion(grafo_pequeno):
    """Las aristas del corte deben cruzar de S a T."""
    _, lado_s, aristas_corte = corte_minimo(grafo_pequeno, "S", "T")
    lado_t = {v for v in grafo_pequeno.ady if v not in lado_s}
    for u, v, _ in aristas_corte:
        assert u in lado_s, f"El extremo {u} debería estar en S"
        assert v in lado_t, f"El extremo {v} debería estar en T"


def test_capacidad_aristas_corte_igual_a_flujo(grafo_pequeno):
    """La suma de capacidades del corte == flujo máximo."""
    valor_flujo, _ = flujo_maximo(grafo_pequeno, "S", "T")
    _, _, aristas_corte = corte_minimo(grafo_pequeno, "S", "T")
    cap_total = sum(c for _, _, c in aristas_corte)
    assert abs(cap_total - valor_flujo) < 1e-6


# ---------------------------------------------------------------------------
# Tests contra networkx (campus real)
# ---------------------------------------------------------------------------

def _a_networkx_capacidad(grafo):
    """Convierte el grafo del campus a un DiGraph de networkx con capacidades."""
    G = nx.DiGraph()
    for v in grafo.ady:
        G.add_node(v)
    for u, v, _ in grafo.aristas():
        cap = grafo.capacidad_de(u, v) or 0.0
        G.add_edge(u, v, capacity=cap)
        G.add_edge(v, u, capacity=cap)
    return G


@pytest.mark.parametrize("s,t", [
    ("CDP", "CDR"),
    ("CDP", "SAL"),
    ("CDP", "SEG"),
])
def test_flujo_maximo_igual_networkx(campus, s, t):
    """El flujo máximo calculado por Edmonds-Karp debe coincidir con networkx."""
    valor_propio, _ = flujo_maximo(campus, s, t)
    G = _a_networkx_capacidad(campus)
    valor_nx = nx.maximum_flow_value(G, s, t, capacity="capacity")
    assert abs(valor_propio - valor_nx) < 1e-6, (
        f"Discrepancia {s}→{t}: propio={valor_propio}, networkx={valor_nx}"
    )


@pytest.mark.parametrize("s,t", [
    ("CDP", "CDR"),
    ("CDP", "SAL"),
])
def test_max_flow_min_cut_campus(campus, s, t):
    """Teorema max-flow/min-cut verificado sobre el campus real."""
    valor_flujo, _ = flujo_maximo(campus, s, t)
    valor_corte, _, _ = corte_minimo(campus, s, t)
    assert abs(valor_flujo - valor_corte) < 1e-6


# ---------------------------------------------------------------------------
# Tests de casos límite y robustez
# ---------------------------------------------------------------------------

def test_flujo_nodo_origen_inexistente(campus):
    with pytest.raises(ValueError, match="no existe"):
        flujo_maximo(campus, "INEXISTENTE", "CDP")


def test_flujo_nodo_destino_inexistente(campus):
    with pytest.raises(ValueError, match="no existe"):
        flujo_maximo(campus, "CDP", "INEXISTENTE")


def test_flujo_origen_igual_destino(campus):
    with pytest.raises(ValueError, match="mismo nodo"):
        flujo_maximo(campus, "CDP", "CDP")


def test_flujo_sin_ruta():
    """Si no hay ruta entre s y t, el flujo debe ser 0."""
    g = Grafo()
    for v in ("A", "B", "C", "D"):
        g.agregar_vertice(v)
    g.agregar_arista("A", "B", peso=1, capacidad=10)
    g.agregar_arista("C", "D", peso=1, capacidad=10)
    valor, _ = flujo_maximo(g, "A", "D")
    assert valor == 0.0


def test_grafo_original_no_modificado_por_flujo(campus):
    """flujo_maximo no debe modificar el grafo original."""
    aristas_antes = set(frozenset((u, v)) for u, v, _ in campus.aristas())
    capacidades_antes = dict(campus.capacidad)
    flujo_maximo(campus, "CDP", "CDR")
    aristas_despues = set(frozenset((u, v)) for u, v, _ in campus.aristas())
    assert aristas_antes == aristas_despues, "Las aristas del grafo fueron modificadas"
    assert campus.capacidad == capacidades_antes, "Las capacidades del grafo fueron modificadas"


def test_grafo_original_no_modificado_por_corte(campus):
    """corte_minimo no debe modificar el grafo original."""
    aristas_antes = set(frozenset((u, v)) for u, v, _ in campus.aristas())
    corte_minimo(campus, "CDP", "CDR")
    aristas_despues = set(frozenset((u, v)) for u, v, _ in campus.aristas())
    assert aristas_antes == aristas_despues


# ---------------------------------------------------------------------------
# Test de pares críticos
# ---------------------------------------------------------------------------

def test_pares_criticos_flujo_positivo(campus):
    """Todos los pares críticos deben tener flujo máximo > 0 en la red completa."""
    pares = cargar_pares_criticos()
    for par in pares:
        valor, _ = flujo_maximo(campus, par["origen"], par["destino"])
        assert valor > 0, (
            f"Flujo 0 para el par crítico {par['origen']}→{par['destino']}"
        )
