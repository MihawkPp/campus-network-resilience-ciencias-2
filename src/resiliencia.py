"""Análisis de resiliencia y propuestas de redundancia.

Funciones principales:
  - componentes_conexos   : identifica grupos de nodos conectados
  - simular_falla_arista  : simula falla de una o más aristas (copia temporal)
  - simular_falla_nodo    : simula falla de un nodo (copia temporal)
  - simular_fallas_aleatorias : fallas con probabilidad p
  - evaluar_pares         : flujo máximo / corte mínimo para cada par crítico
  - proponer_enlaces      : ranking de aristas candidatas por costo-beneficio

IMPORTANTE: Ninguna función modifica el grafo original. Todas trabajan sobre
copias obtenidas con grafo.copiar().
"""

import random

from .grafo import es_conexo
from .flujo import flujo_maximo, corte_minimo


# ---------------------------------------------------------------------------
# Utilidades de conectividad
# ---------------------------------------------------------------------------

def componentes_conexos(grafo):
    """Devuelve lista de conjuntos; cada conjunto es un componente conexo."""
    visitado = set()
    componentes = []
    for inicio in grafo.ady:
        if inicio in visitado:
            continue
        comp = set()
        pila = [inicio]
        while pila:
            u = pila.pop()
            if u in comp:
                continue
            comp.add(u)
            for v in grafo.ady[u]:
                if v not in comp:
                    pila.append(v)
        visitado |= comp
        componentes.append(comp)
    return componentes


def nodos_desconectados(grafo, origen):
    """Cantidad de vértices que NO se alcanzan desde `origen`."""
    if origen not in grafo.ady:
        return len(grafo.ady)
    visitados = {origen}
    pendientes = [origen]
    while pendientes:
        u = pendientes.pop()
        for v in grafo.ady[u]:
            if v not in visitados:
                visitados.add(v)
                pendientes.append(v)
    return len(grafo.ady) - len(visitados)


def _nodos_criticos(grafo):
    """Nodos marcados como críticos en grafo.info."""
    return [v for v, info in grafo.info.items() if info.get("critico")]


# ---------------------------------------------------------------------------
# Resumen de estado de la red
# ---------------------------------------------------------------------------

def _resumen_red(grafo, pares_criticos, etiqueta="Red"):
    """Calcula métricas de estado de la red y las devuelve como dict."""
    comps = componentes_conexos(grafo)
    nodos_totales = len(grafo.ady)
    aristas_totales = len(grafo.aristas())
    criticos = _nodos_criticos(grafo)
    criticos_en_grafo = [c for c in criticos if c in grafo.ady]

    # ¿Cuántos pares críticos siguen conectados?
    pares_ok, pares_flujo = [], []
    for par in pares_criticos:
        s, t = par["origen"], par["destino"]
        if s not in grafo.ady or t not in grafo.ady:
            pares_flujo.append({**par, "flujo": 0.0, "cubre": False, "aislado": True})
            continue
        # Verificar si están en el mismo componente
        mismo_comp = any(s in c and t in c for c in comps)
        if not mismo_comp:
            pares_flujo.append({**par, "flujo": 0.0, "cubre": False, "aislado": True})
            continue
        try:
            flujo, _ = flujo_maximo(grafo, s, t)
        except (ValueError, KeyError):
            flujo = 0.0
        cubre = flujo >= par["demanda_gbps"]
        pares_flujo.append({**par, "flujo": flujo, "cubre": cubre, "aislado": False})
        if cubre:
            pares_ok.append(par)

    # Nodos aislados (componentes de tamaño 1)
    nodos_aislados = [list(c)[0] for c in comps if len(c) == 1]

    return {
        "etiqueta": etiqueta,
        "nodos": nodos_totales,
        "aristas": aristas_totales,
        "componentes": len(comps),
        "nodos_aislados": nodos_aislados,
        "criticos_presentes": criticos_en_grafo,
        "criticos_faltantes": [c for c in criticos if c not in grafo.ady],
        "pares_flujo": pares_flujo,
        "pares_cubiertos": len(pares_ok),
        "pares_total": len(pares_criticos),
    }


# ---------------------------------------------------------------------------
# Simulaciones de falla (siempre sobre copias)
# ---------------------------------------------------------------------------

def simular_falla_arista(grafo, pares_criticos, u, v):
    """Simula la falla de la arista u--v.

    Parámetros
    ----------
    grafo         : Grafo original (no se modifica)
    pares_criticos: lista de dicts con origen, destino, demanda_gbps
    u, v          : extremos de la arista a eliminar

    Devuelve
    --------
    (original, despues) : dos dicts de resumen de la red
    """
    copia = grafo.copiar()
    if v not in copia.ady.get(u, {}):
        raise ValueError(f"La arista {u}--{v} no existe en el grafo.")
    copia.quitar_arista(u, v)

    original = _resumen_red(grafo, pares_criticos, "Original")
    despues = _resumen_red(copia, pares_criticos, f"Tras falla {u}--{v}")
    return original, despues


def simular_falla_multiples_aristas(grafo, pares_criticos, aristas):
    """Simula la falla simultánea de varias aristas.

    Parámetros
    ----------
    aristas : lista de (u, v)
    """
    copia = grafo.copiar()
    eliminadas = []
    errores = []
    for u, v in aristas:
        try:
            copia.quitar_arista(u, v)
            eliminadas.append((u, v))
        except ValueError as e:
            errores.append(str(e))

    etiqueta = f"Tras falla de {len(eliminadas)} aristas"
    original = _resumen_red(grafo, pares_criticos, "Original")
    despues = _resumen_red(copia, pares_criticos, etiqueta)
    despues["errores"] = errores
    despues["eliminadas"] = eliminadas
    return original, despues


def simular_falla_nodo(grafo, pares_criticos, nodo):
    """Simula la falla de un nodo (y todas sus aristas).

    Parámetros
    ----------
    nodo : str — identificador del nodo a eliminar
    """
    if nodo not in grafo.ady:
        raise ValueError(f"El nodo '{nodo}' no existe en el grafo.")
    copia = grafo.copiar()
    copia.eliminar_vertice(nodo)

    # Pares críticos que involucran el nodo eliminado se marcan como aislados
    pares_ajustados = list(pares_criticos)

    original = _resumen_red(grafo, pares_criticos, "Original")
    despues = _resumen_red(copia, pares_ajustados, f"Tras falla del nodo '{nodo}'")
    return original, despues


def simular_fallas_aleatorias(grafo, pares_criticos, probabilidad, semilla=None):
    """Simula fallas aleatorias de aristas con probabilidad `p` cada una.

    Parámetros
    ----------
    probabilidad : float en [0, 1]
    semilla      : int opcional para reproducibilidad

    Devuelve
    --------
    (original, despues, eliminadas) : resúmenes y lista de aristas eliminadas
    """
    if not 0.0 <= probabilidad <= 1.0:
        raise ValueError("La probabilidad debe estar en [0, 1].")
    rng = random.Random(semilla)
    copia = grafo.copiar()
    eliminadas = []
    for u, v, _ in grafo.aristas():
        if rng.random() < probabilidad:
            try:
                copia.quitar_arista(u, v)
                eliminadas.append((u, v))
            except ValueError:
                pass  # ya fue eliminada (arista duplicada en iteración)

    original = _resumen_red(grafo, pares_criticos, "Original")
    etiqueta = f"Tras fallas aleatorias (p={probabilidad:.0%}, {len(eliminadas)} aristas)"
    despues = _resumen_red(copia, pares_criticos, etiqueta)
    despues["eliminadas"] = eliminadas
    return original, despues, eliminadas


# ---------------------------------------------------------------------------
# Evaluación de pares críticos sobre el grafo completo
# ---------------------------------------------------------------------------

def evaluar_pares(grafo, pares_criticos):
    """Para cada par crítico: flujo máximo, corte mínimo y si cubre la demanda.

    Devuelve lista de dicts con las métricas de cada par.
    """
    comps = componentes_conexos(grafo)
    resultados = []
    for par in pares_criticos:
        s, t = par["origen"], par["destino"]
        mismo_comp = any(s in c and t in c for c in comps)
        if not mismo_comp or s not in grafo.ady or t not in grafo.ady:
            resultados.append({
                **par,
                "flujo_maximo": 0.0,
                "corte_capacidad": 0.0,
                "aristas_corte": [],
                "cubre_demanda": False,
                "mensaje": "Sin ruta (nodos desconectados)",
            })
            continue
        try:
            flujo, _ = flujo_maximo(grafo, s, t)
            corte_cap, lado_s, aristas_corte = corte_minimo(grafo, s, t)
        except (ValueError, KeyError) as e:
            resultados.append({
                **par,
                "flujo_maximo": 0.0,
                "corte_capacidad": 0.0,
                "aristas_corte": [],
                "cubre_demanda": False,
                "mensaje": str(e),
            })
            continue
        resultados.append({
            **par,
            "flujo_maximo": flujo,
            "corte_capacidad": corte_cap,
            "aristas_corte": aristas_corte,
            "cubre_demanda": flujo >= par["demanda_gbps"],
            "mensaje": "OK",
        })
    return resultados


# ---------------------------------------------------------------------------
# Propuesta de redundancia
# ---------------------------------------------------------------------------

def proponer_enlaces(grafo, mst_aristas, pares_criticos, top_n=5):
    """Evalúa aristas candidatas no incluidas en el MST y recomienda las mejores.

    Estrategia greedy por relación costo-beneficio:
      beneficio = suma de mejoras de flujo máximo en todos los pares críticos
      costo     = costo_total_usd de la arista candidata
      razón     = beneficio / costo

    Parámetros
    ----------
    grafo         : Grafo completo del campus
    mst_aristas   : lista de (u, v, peso) del MST
    pares_criticos: lista de dicts con origen, destino, demanda_gbps
    top_n         : cuántas propuestas devolver

    Devuelve
    --------
    lista de dicts ordenados de mayor a menor razón costo-beneficio
    """
    # Aristas ya presentes en el MST
    mst_set = {frozenset((u, v)) for u, v, _ in mst_aristas}

    # Grafo del MST (para medir flujo sobre la red mínima)
    grafo_mst = grafo.subgrafo_con_aristas(mst_aristas)

    # Flujos base sobre el MST para cada par
    flujos_base = {}
    comps_base = componentes_conexos(grafo_mst)
    for par in pares_criticos:
        s, t = par["origen"], par["destino"]
        mismo_comp = any(s in c and t in c for c in comps_base)
        if not mismo_comp:
            flujos_base[(s, t)] = 0.0
            continue
        try:
            f, _ = flujo_maximo(grafo_mst, s, t)
            flujos_base[(s, t)] = f
        except (ValueError, KeyError):
            flujos_base[(s, t)] = 0.0

    costo_mst = sum(p for _, _, p in mst_aristas)

    # Evaluar cada arista candidata que no está en el MST
    candidatas = [
        (u, v, peso) for u, v, peso in grafo.aristas()
        if frozenset((u, v)) not in mst_set
    ]

    propuestas = []
    for u, v, costo_enlace in candidatas:
        cap = grafo.capacidad_de(u, v) or 0.0
        if cap <= 0:
            continue

        # Construir MST + este enlace
        mst_mas_enlace = list(mst_aristas) + [(u, v, costo_enlace)]
        grafo_ampliado = grafo.subgrafo_con_aristas(mst_mas_enlace)

        # Calcular flujos con el nuevo enlace
        mejora_total = 0.0
        detalle_pares = []
        comps_amp = componentes_conexos(grafo_ampliado)
        for par in pares_criticos:
            s, t = par["origen"], par["destino"]
            mismo_comp = any(s in c and t in c for c in comps_amp)
            if not mismo_comp:
                f_nuevo = 0.0
            else:
                try:
                    f_nuevo, _ = flujo_maximo(grafo_ampliado, s, t)
                except (ValueError, KeyError):
                    f_nuevo = 0.0
            f_base = flujos_base.get((s, t), 0.0)
            delta = max(0.0, f_nuevo - f_base)
            mejora_total += delta
            detalle_pares.append({
                "par": f"{s}→{t}",
                "flujo_base": f_base,
                "flujo_nuevo": f_nuevo,
                "delta": delta,
            })

        razon = mejora_total / costo_enlace if costo_enlace > 0 else 0.0

        # Corte mínimo con el enlace añadido (usar par crítico más demandante)
        par_ref = max(pares_criticos, key=lambda p: p["demanda_gbps"])
        s_ref, t_ref = par_ref["origen"], par_ref["destino"]
        mismo_comp_ref = any(s_ref in c and t_ref in c for c in comps_amp)
        if mismo_comp_ref:
            try:
                corte_cap_nuevo, _, _ = corte_minimo(grafo_ampliado, s_ref, t_ref)
            except (ValueError, KeyError):
                corte_cap_nuevo = 0.0
        else:
            corte_cap_nuevo = 0.0

        mismo_comp_base = any(s_ref in c and t_ref in c for c in comps_base)
        if mismo_comp_base:
            try:
                corte_cap_base, _, _ = corte_minimo(grafo_mst, s_ref, t_ref)
            except (ValueError, KeyError):
                corte_cap_base = 0.0
        else:
            corte_cap_base = 0.0

        propuestas.append({
            "u": u,
            "v": v,
            "capacidad_gbps": cap,
            "costo_enlace_usd": costo_enlace,
            "costo_mst_usd": costo_mst,
            "costo_total_usd": costo_mst + costo_enlace,
            "mejora_flujo_gbps": mejora_total,
            "razon_beneficio_costo": razon,
            "corte_base_gbps": corte_cap_base,
            "corte_nuevo_gbps": corte_cap_nuevo,
            "delta_corte_gbps": corte_cap_nuevo - corte_cap_base,
            "detalle_pares": detalle_pares,
        })

    # Ordenar de mayor a menor razón beneficio/costo
    propuestas.sort(key=lambda p: p["razon_beneficio_costo"], reverse=True)
    return propuestas[:top_n]


__all__ = [
    "componentes_conexos",
    "nodos_desconectados",
    "simular_falla_arista",
    "simular_falla_multiples_aristas",
    "simular_falla_nodo",
    "simular_fallas_aleatorias",
    "evaluar_pares",
    "proponer_enlaces",
]
