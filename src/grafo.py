"""Grafo no dirigido ponderado (costo) con capacidades opcionales por arista.

Basado en la clase Grafo original del proyecto. Cambios:
  - cada arista puede guardar una capacidad (Gbps) además del peso (costo);
  - se pueden guardar coordenadas de los vértices (para dibujar);
  - métodos copiar() y quitar_arista() para simular fallas.
"""


class Grafo:
    def __init__(self):
        self.ady = {}         # ady[u][v] = peso (costo)
        self.capacidad = {}   # capacidad[frozenset({u, v})] = capacidad
        self.pos = {}         # pos[v] = (x, y)
        self.info = {}        # info[v] = dict con atributos extra del nodo

    # ---------- vértices ----------
    def agregar_vertice(self, v, pos=None, **info):
        if not v:
            raise ValueError("El nombre del vértice no puede estar vacío.")
        if v in self.ady:
            raise ValueError(f"El vértice '{v}' ya existe.")
        self.ady[v] = {}
        if pos is not None:
            self.pos[v] = pos
        self.info[v] = info

    def eliminar_vertice(self, v):
        if v not in self.ady:
            raise ValueError(f"El vértice '{v}' no existe.")
        for w in list(self.ady[v]):
            self.capacidad.pop(frozenset((v, w)), None)
        del self.ady[v]
        for vecinos in self.ady.values():
            vecinos.pop(v, None)
        self.pos.pop(v, None)
        self.info.pop(v, None)

    # ---------- aristas ----------
    def agregar_arista(self, u, v, peso, capacidad=None):
        if u not in self.ady or v not in self.ady:
            raise ValueError("Ambos vértices deben existir.")
        if u == v:
            raise ValueError("No se permiten aristas de un vértice a sí mismo.")
        if v in self.ady[u]:
            raise ValueError(f"La arista {u}--{v} ya existe.")
        self.ady[u][v] = peso
        self.ady[v][u] = peso
        if capacidad is not None:
            self.capacidad[frozenset((u, v))] = capacidad

    def quitar_arista(self, u, v):
        if v not in self.ady.get(u, {}):
            raise ValueError(f"La arista {u}--{v} no existe.")
        del self.ady[u][v]
        del self.ady[v][u]
        self.capacidad.pop(frozenset((u, v)), None)

    def capacidad_de(self, u, v):
        return self.capacidad.get(frozenset((u, v)))

    def aristas(self):
        resultado = []
        for u, vecinos in self.ady.items():
            for v, peso in vecinos.items():
                if u < v:
                    resultado.append((u, v, peso))
        return resultado

    def costo_total(self):
        return sum(p for _, _, p in self.aristas())

    # ---------- utilidades ----------
    def copiar(self):
        g = Grafo()
        g.ady = {u: dict(vec) for u, vec in self.ady.items()}
        g.capacidad = dict(self.capacidad)
        g.pos = dict(self.pos)
        g.info = {v: dict(d) for v, d in self.info.items()}
        return g

    def subgrafo_con_aristas(self, aristas):
        """Grafo con los mismos vértices y solo las aristas indicadas (u, v, peso).

        Útil para construir el grafo del MST conservando capacidades y posiciones.
        """
        g = Grafo()
        for v in self.ady:
            g.agregar_vertice(v, self.pos.get(v), **self.info.get(v, {}))
        for u, v, peso in aristas:
            g.agregar_arista(u, v, peso, self.capacidad_de(u, v))
        return g

    def mostrar(self):
        if not self.ady:
            print("  (grafo vacío)")
        for u, vecinos in self.ady.items():
            lista = ", ".join(f"{v}(peso={p:g})" for v, p in vecinos.items()) or "∅"
            print(f"  {u} -> [{lista}]")


def es_conexo(grafo):
    if not grafo.ady:
        return False
    inicio = next(iter(grafo.ady))
    visitados = {inicio}
    pendientes = [inicio]
    while pendientes:
        u = pendientes.pop()
        for v in grafo.ady[u]:
            if v not in visitados:
                visitados.add(v)
                pendientes.append(v)
    return len(visitados) == len(grafo.ady)


def validar_conexo(grafo):
    if not grafo.ady:
        raise ValueError("El grafo no tiene vértices.")
    if not es_conexo(grafo):
        raise ValueError("El grafo no está conectado; no tiene árbol de expansión.")
