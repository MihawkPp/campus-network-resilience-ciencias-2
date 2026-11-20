"""
Genera data/enlaces_candidatos.csv a partir de data/nodos.csv.

Todas las reglas son deterministas (no hay aleatoriedad), de modo que el
dataset es reproducible y cada costo se puede justificar en el informe.

Reglas:
  1. Solo se consideran enlaces entre nodos a <= DIST_MAX metros
     (más lejos no es viable tender fibra directa).
  2. Costo de obra = distancia * costo por metro según canalización:
       - ducto_existente: hay ducto entre centros de datos y hubs.
       - zanja_nueva:     el resto de enlaces.
  3. Si el enlace cruza la Avenida Interna (x = X_AVENIDA) se suma un
     costo fijo por permisos y obra de cruce vial.
  4. Capacidad según la jerarquía de los extremos:
       - troncal      (núcleo <-> núcleo):    100 Gbps
       - distribución (núcleo <-> edificio):   40 Gbps
       - acceso       (edificio <-> edificio): 10 Gbps
     donde núcleo = centro de datos o hub.
  5. Costo de equipos (transceptores en ambos extremos) según capacidad.
  6. costo_total_usd = obra + cruce + equipos   ->  es el PESO para el MST.

Uso:
    python scripts/generar_enlaces.py
"""

import csv
import math
from itertools import combinations
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_NODOS = RAIZ / "data" / "nodos.csv"
ARCHIVO_ENLACES = RAIZ / "data" / "enlaces_candidatos.csv"

DIST_MAX = 270          # metros
X_AVENIDA = 520         # la Avenida Interna corre de norte a sur en x = 520
COSTO_CRUCE_VIAL = 8000  # USD fijos por cruzar la avenida

COSTO_POR_METRO = {      # USD por metro
    "ducto_existente": 12,
    "zanja_nueva": 45,
}
CAPACIDAD = {"troncal": 100, "distribucion": 40, "acceso": 10}           # Gbps
COSTO_EQUIPOS = {"troncal": 3000, "distribucion": 1200, "acceso": 400}   # USD

NUCLEO = {"centro_datos", "hub"}


def leer_nodos():
    with open(ARCHIVO_NODOS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def nivel_enlace(tipo_a, tipo_b):
    nucleos = (tipo_a in NUCLEO) + (tipo_b in NUCLEO)
    return {2: "troncal", 1: "distribucion", 0: "acceso"}[nucleos]


def generar():
    nodos = leer_nodos()
    filas = []
    for a, b in combinations(nodos, 2):
        xa, ya, xb, yb = (float(a["x_m"]), float(a["y_m"]),
                          float(b["x_m"]), float(b["y_m"]))
        distancia = math.hypot(xa - xb, ya - yb)
        if distancia > DIST_MAX:
            continue

        nivel = nivel_enlace(a["tipo"], b["tipo"])
        canalizacion = "ducto_existente" if nivel == "troncal" else "zanja_nueva"
        cruza_avenida = (xa - X_AVENIDA) * (xb - X_AVENIDA) < 0

        costo_obra = distancia * COSTO_POR_METRO[canalizacion]
        costo_cruce = COSTO_CRUCE_VIAL if cruza_avenida else 0
        costo_equipos = COSTO_EQUIPOS[nivel]
        costo_total = round(costo_obra + costo_cruce + costo_equipos)

        filas.append({
            "origen": a["id"],
            "destino": b["id"],
            "distancia_m": round(distancia, 1),
            "nivel": nivel,
            "canalizacion": canalizacion,
            "cruza_avenida": "si" if cruza_avenida else "no",
            "capacidad_gbps": CAPACIDAD[nivel],
            "costo_obra_usd": round(costo_obra),
            "costo_cruce_usd": costo_cruce,
            "costo_equipos_usd": costo_equipos,
            "costo_total_usd": costo_total,
        })

    filas.sort(key=lambda f: (f["origen"], f["destino"]))
    with open(ARCHIVO_ENLACES, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"{len(filas)} enlaces candidatos escritos en {ARCHIVO_ENLACES.relative_to(RAIZ)}")


if __name__ == "__main__":
    generar()
