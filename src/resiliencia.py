"""Análisis de resiliencia y propuestas de redundancia (Tareas 2 y 3).  -- POR IMPLEMENTAR --

Depende de src/flujo.py. Las funciones de abajo son el plan de trabajo.
"""

from .grafo import es_conexo


def nodos_desconectados(grafo, origen):
    """Cantidad de vértices que NO se alcanzan desde `origen`. (Implementada: base para fallas.)"""
    visitados = {origen}
    pendientes = [origen]
    while pendientes:
        u = pendientes.pop()
        for v in grafo.ady[u]:
            if v not in visitados:
                visitados.add(v)
                pendientes.append(v)
    return len(grafo.ady) - len(visitados)


def simular_fallas(red, pares_criticos, origen="CDP"):
    """Quita cada arista de `red`, una a la vez, y mide el impacto.

    Para cada arista devolver, por ejemplo:
      - nodos que pierden conexión con `origen`
      - demanda (Gbps) que queda sin servicio
      - cuántos pares críticos quedan con flujo < demanda
    Ordenar de mayor a menor impacto -> ranking de enlaces críticos.
    """
    raise NotImplementedError


def evaluar_pares(red, pares_criticos):
    """Para cada par crítico: flujo máximo, corte mínimo y si cubre la demanda."""
    raise NotImplementedError


def proponer_enlaces(red, candidatos, pares_criticos, presupuesto_usd):
    """Algoritmo voraz de redundancia.

    Mientras haya presupuesto:
      1. para cada enlace candidato que no esté en `red`, calcular
         ganancia = mejora de resiliencia (p. ej., reducción del impacto de la
         peor falla, o aumento del flujo en pares críticos)
         razon = ganancia / costo
      2. agregar el de mejor razón y registrar costo acumulado y métricas.
    Devolver la lista de enlaces agregados con sus métricas (curva costo vs. robustez).
    """
    raise NotImplementedError


__all__ = ["es_conexo", "nodos_desconectados", "simular_fallas",
           "evaluar_pares", "proponer_enlaces"]
