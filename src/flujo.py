"""Flujo máximo y corte mínimo — Edmonds-Karp (Ford-Fulkerson con BFS).

Modelado de la red no dirigida:
  Cada arista u--v con capacidad c se convierte en DOS arcos dirigidos:
    u → v con capacidad c
    v → u con capacidad c
  La red residual `res[u][v]` guarda la capacidad residual (disponible) de u→v.
  Cuando se envía flujo f por u→v se hace:
    res[u][v] -= f
    res[v][u] += f   (arco inverso para cancelar flujo)

Complejidad de Edmonds-Karp: O(V · E²)
"""

from collections import deque


# ---------------------------------------------------------------------------
# Construcción de la red residual inicial
# ---------------------------------------------------------------------------

def _red_residual(grafo):
    """Construye la red residual inicial a partir de un Grafo no dirigido.

    Para cada arista u--v con capacidad c (Gbps), añade:
      res[u][v] = c   (capacidad directa)
      res[v][u] = c   (capacidad directa en el sentido contrario)
    Si una arista no tiene capacidad definida se le asigna 0 (no transporta flujo).
    """
    res = {v: {} for v in grafo.ady}
    for u, v, _ in grafo.aristas():
        cap = grafo.capacidad_de(u, v) or 0.0
        # Añadir en ambas direcciones (grafo no dirigido → cada sentido es independiente)
        res[u][v] = res[u].get(v, 0.0) + cap
        res[v][u] = res[v].get(u, 0.0) + cap
    return res


# ---------------------------------------------------------------------------
# BFS para hallar camino aumentante (Edmonds-Karp)
# ---------------------------------------------------------------------------

def _bfs(res, s, t):
    """BFS en la red residual desde s hasta t.

    Devuelve el dict `predecesor` si existe camino s→t, o None en caso contrario.
    Solo se atraviesan arcos con capacidad residual > 0.
    """
    cola = deque([s])
    predecesor = {s: None}
    while cola:
        u = cola.popleft()
        for v, cap in res[u].items():
            if v not in predecesor and cap > 1e-9:
                predecesor[v] = u
                if v == t:
                    return predecesor
                cola.append(v)
    return None


# ---------------------------------------------------------------------------
# Edmonds-Karp
# ---------------------------------------------------------------------------

def flujo_maximo(grafo, s, t):
    """Calcula el flujo máximo de s a t mediante Edmonds-Karp.

    Parámetros
    ----------
    grafo : Grafo
        Grafo no dirigido con capacidades (Gbps) en grafo.capacidad.
    s, t  : str
        Nodo de origen (source) y destino (sink).

    Devuelve
    --------
    valor : float
        Valor del flujo máximo (Gbps).
    res   : dict[str, dict[str, float]]
        Red residual final, útil para identificar el corte mínimo.

    Lanza
    -----
    ValueError
        Si s o t no existen en el grafo, o si s == t.
    """
    if s not in grafo.ady:
        raise ValueError(f"El nodo origen '{s}' no existe en el grafo.")
    if t not in grafo.ady:
        raise ValueError(f"El nodo destino '{t}' no existe en el grafo.")
    if s == t:
        raise ValueError("El origen y el destino no pueden ser el mismo nodo.")

    res = _red_residual(grafo)
    valor = 0.0

    while True:
        pred = _bfs(res, s, t)
        if pred is None:
            break  # No hay más caminos aumentantes → flujo máximo alcanzado

        # Calcular el flujo del camino (cuello de botella)
        flujo_camino = float("inf")
        v = t
        while v != s:
            u = pred[v]
            flujo_camino = min(flujo_camino, res[u][v])
            v = u

        # Actualizar la red residual
        v = t
        while v != s:
            u = pred[v]
            res[u][v] -= flujo_camino
            res[v][u] += flujo_camino
            v = u

        valor += flujo_camino

    return valor, res


# ---------------------------------------------------------------------------
# Corte mínimo
# ---------------------------------------------------------------------------

def corte_minimo(grafo, s, t):
    """Identifica el corte mínimo correspondiente al flujo máximo s→t.

    Aplica el Teorema Max-Flow/Min-Cut:
    Los nodos alcanzables desde s en la red residual final forman el
    conjunto S; los demás forman T.  Las aristas que cruzan de S hacia T
    (con capacidad residual ≈ 0, es decir, saturadas) conforman el corte.

    Devuelve
    --------
    valor_corte : float
        Capacidad total del corte (igual al flujo máximo).
    lado_s      : set[str]
        Conjunto de nodos en el lado S del corte.
    aristas_corte : list[tuple[str, str, float]]
        Lista de (u, v, capacidad_original) con u ∈ S y v ∈ T.
    """
    valor_corte, res = flujo_maximo(grafo, s, t)

    # BFS en la red residual final para hallar el conjunto S
    lado_s = set()
    cola = deque([s])
    lado_s.add(s)
    while cola:
        u = cola.popleft()
        for v, cap in res[u].items():
            if v not in lado_s and cap > 1e-9:
                lado_s.add(v)
                cola.append(v)

    # Las aristas del corte son las que cruzan de S a T con capacidad original > 0
    aristas_corte = []
    for u, v, _ in grafo.aristas():
        cap = grafo.capacidad_de(u, v) or 0.0
        if cap > 0:
            # La arista cruza el corte si un extremo está en S y el otro en T
            if u in lado_s and v not in lado_s:
                aristas_corte.append((u, v, cap))
            elif v in lado_s and u not in lado_s:
                aristas_corte.append((v, u, cap))

    return valor_corte, lado_s, aristas_corte
