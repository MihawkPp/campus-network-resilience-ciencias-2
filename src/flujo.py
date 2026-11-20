"""Flujo máximo y corte mínimo (Tarea 2 del proyecto).  -- POR IMPLEMENTAR --

Idea:
  - Cada arista no dirigida u--v con capacidad c se modela como dos arcos
    dirigidos u->v y v->u, ambos con capacidad c.
  - Edmonds-Karp: Ford-Fulkerson usando BFS para hallar caminos aumentantes.
  - Al terminar, los vértices alcanzables desde s en la red residual forman el
    lado S del corte mínimo; las aristas que cruzan de S a T son el corte.

Validación sugerida (tests/test_flujo.py):
  comparar con networkx.maximum_flow_value y networkx.minimum_cut.
"""


def flujo_maximo(grafo, s, t):
    """Devuelve (valor_flujo, flujo) donde flujo[(u, v)] es lo que pasa por u->v.

    Usar grafo.capacidad_de(u, v) como capacidad de cada dirección.
    """
    raise NotImplementedError("Implementar Edmonds-Karp")


def corte_minimo(grafo, s, t):
    """Devuelve (valor_corte, lado_s, aristas_corte).

    lado_s: conjunto de vértices alcanzables desde s en la red residual.
    aristas_corte: lista de (u, v, capacidad) con u en lado_s y v fuera.
    Por el teorema max-flow/min-cut, valor_corte == valor del flujo máximo.
    """
    raise NotImplementedError("Implementar a partir de la red residual de flujo_maximo")
