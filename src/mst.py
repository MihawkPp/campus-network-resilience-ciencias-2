"""Algoritmos de árbol de expansión mínima (Tarea 1 del proyecto).

Prim y Kruskal tomados del código original del proyecto, sin cambios en la lógica.
Ambos devuelven (arbol, pasos):
  arbol: lista de aristas (u, v, peso)
  pasos: descripción textual de cada decisión (útil para el informe)
"""

import time

from .grafo import validar_conexo


def prim(grafo):
    validar_conexo(grafo)
    inicio = next(iter(grafo.ady))
    visitados = {inicio}
    arbol = []
    pasos = [f"Comenzar en el vértice {inicio}."]
    while len(visitados) < len(grafo.ady):
        candidatas = [
            (peso, u, v) for u in visitados
            for v, peso in grafo.ady[u].items() if v not in visitados
        ]
        peso, u, v = min(candidatas)
        arbol.append((u, v, peso))
        visitados.add(v)
        pasos.append(f"Elegir {u}--{v}, peso {peso:g}; añadir {v} al árbol.")
    return arbol, pasos


def kruskal(grafo):
    validar_conexo(grafo)
    padre = {v: v for v in grafo.ady}
    rango = {v: 0 for v in grafo.ady}

    def buscar(v):
        if padre[v] != v:
            padre[v] = buscar(padre[v])
        return padre[v]

    def unir(a, b):
        ra, rb = buscar(a), buscar(b)
        if ra == rb:
            return False
        if rango[ra] < rango[rb]:
            ra, rb = rb, ra
        padre[rb] = ra
        if rango[ra] == rango[rb]:
            rango[ra] += 1
        return True

    arbol, pasos = [], []
    for u, v, peso in sorted(grafo.aristas(), key=lambda e: (e[2], e[0], e[1])):
        if unir(u, v):
            arbol.append((u, v, peso))
            pasos.append(f"Aceptar {u}--{v}, peso {peso:g}; no forma un ciclo.")
        else:
            pasos.append(f"Descartar {u}--{v}, peso {peso:g}; formaría un ciclo.")
        if len(arbol) == len(grafo.ady) - 1:
            break
    return arbol, pasos


def comparar(grafo):
    """Ejecuta ambos algoritmos y devuelve un dict con costo, tiempo y aristas."""
    resultado = {}
    for nombre, algoritmo in (("prim", prim), ("kruskal", kruskal)):
        t0 = time.perf_counter()
        arbol, _ = algoritmo(grafo)
        ms = (time.perf_counter() - t0) * 1000
        resultado[nombre] = {
            "arbol": arbol,
            "costo": sum(p for _, _, p in arbol),
            "tiempo_ms": ms,
            "aristas": {frozenset((u, v)) for u, v, _ in arbol},
        }
    resultado["mismo_costo"] = resultado["prim"]["costo"] == resultado["kruskal"]["costo"]
    resultado["mismas_aristas"] = resultado["prim"]["aristas"] == resultado["kruskal"]["aristas"]
    return resultado
