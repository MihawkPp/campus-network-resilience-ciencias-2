# Proyecto 4: Robustez de infraestructura y diseño de redundancia

Diseño de una red de fibra óptica de costo mínimo (MST) para un campus universitario
y evaluación de su resiliencia ante fallas mediante flujo máximo / corte mínimo.

## Estructura

```
proyecto-redundancia/
├── main.py                     Menú de consola (punto de entrada)
├── requirements.txt
├── data/
│   ├── nodos.csv               18 nodos: centros de datos, hubs y edificios
│   ├── enlaces_candidatos.csv  54 enlaces posibles con costo y capacidad (generado)
│   └── pares_criticos.csv      7 pares origen-destino con demanda y prioridad
├── scripts/
│   └── generar_enlaces.py      Reglas que producen enlaces_candidatos.csv
├── src/
│   ├── grafo.py                Clase Grafo (peso + capacidad + posición)
│   ├── datos.py                Carga de los CSV a un Grafo
│   ├── mst.py                  Prim y Kruskal                         [Tarea 1 ✔]
│   ├── flujo.py                Edmonds-Karp y corte mínimo            [Tarea 2 – pendiente]
│   ├── resiliencia.py          Fallas, pares críticos, propuestas     [Tareas 2-3 – pendiente]
│   └── visualizacion.py        Dibujo del campus, MST, críticos, propuestos
├── tests/
│   └── test_mst.py             Valida Prim/Kruskal contra networkx
├── notebooks/                  Notebook de análisis (para el informe)
├── resultados/
│   ├── figuras/                PNG generados
│   └── tablas/                 CSV de resultados (fallas, costo-beneficio)
└── informe/                    Informe final costo-beneficio
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
python main.py                      # menú
python -m pytest                    # pruebas
python scripts/generar_enlaces.py   # regenerar enlaces si cambian nodos o reglas
```

## Escenario

Un campus de unos 800 × 600 m necesita una red de fibra que conecte 12 edificios,
4 cuartos de telecomunicaciones (hubs) y 2 centros de datos. Una **Avenida Interna**
(x = 520 m) divide el campus: cruzarla exige permisos y obra civil, por lo que cuesta
USD 8.000 adicionales por enlace.

## Diccionario de datos

### `data/nodos.csv`
| Columna | Descripción |
|---|---|
| `id` | Identificador corto (CDP, HN, BIB…) |
| `nombre` | Nombre del edificio |
| `tipo` | `centro_datos`, `hub` o `edificio` |
| `x_m`, `y_m` | Posición en metros dentro del plano del campus |
| `demanda_gbps` | Tráfico pico que el edificio consume (0 en núcleo) |
| `critico` | `si` si su desconexión es inaceptable (clínica, seguridad, centros de datos) |

### `data/enlaces_candidatos.csv`
Generado por `scripts/generar_enlaces.py` con reglas deterministas:

| Columna | Descripción / regla |
|---|---|
| `origen`, `destino` | Extremos del enlace (solo pares a ≤ 270 m) |
| `distancia_m` | Distancia euclidiana |
| `nivel` | `troncal` (núcleo↔núcleo), `distribucion` (núcleo↔edificio), `acceso` (edificio↔edificio) |
| `canalizacion` | `ducto_existente` (troncales, USD 12/m) o `zanja_nueva` (USD 45/m) |
| `cruza_avenida` | `si` si atraviesa la Avenida Interna |
| `capacidad_gbps` | 100 / 40 / 10 según el nivel → **capacidad para flujo máximo** |
| `costo_obra_usd` | distancia × costo por metro |
| `costo_cruce_usd` | 8.000 si cruza la avenida, 0 si no |
| `costo_equipos_usd` | Transceptores: 3.000 / 1.200 / 400 según el nivel |
| `costo_total_usd` | Suma de los tres → **peso para el MST** |

### `data/pares_criticos.csv`
| Columna | Descripción |
|---|---|
| `origen`, `destino` | Par a evaluar con flujo máximo / corte mínimo |
| `demanda_gbps` | Tráfico que la red debe poder transportar entre ellos |
| `prioridad` | `alta`, `media`, `baja` |
| `justificacion` | Por qué el par importa |

## Resultados actuales (Tarea 1)

| | Valor |
|---|---|
| Costo de construir los 54 enlaces | USD 546.916 |
| Costo del MST (17 enlaces) | **USD 120.230** (22 %) |
| Prim = Kruskal | Sí, mismo costo y mismas aristas |
| Conectividad del grafo candidato | 3 (hay que cortar 3 enlaces para partirlo) |
| Conectividad del MST | 1 (cualquier falla lo parte) |

Hallazgo inicial: el MST cruza la avenida por un **único enlace (CDP–HE)**. Todo el
lado este (laboratorios, ingeniería, ciencias, seguridad y el centro de respaldo)
depende de él. La clínica (SAL) llega por una cadena de enlaces de acceso de 10 Gbps
(HO–BIB–RES–SAL).

## Plan de trabajo

1. ~~MST con Prim y Kruskal~~
2. `src/flujo.py`: Edmonds-Karp + corte mínimo, validado contra networkx.
3. `src/resiliencia.py`:
   - flujo y corte de cada par crítico sobre el MST;
   - simulación de falla de cada enlace → ranking de enlaces críticos.
4. `src/resiliencia.py`: algoritmo voraz que agrega enlaces por mejor razón
   (mejora de resiliencia / costo), con curva costo vs. robustez.
5. Comparar tres escenarios: MST, MST + redundancia, grafo completo.
6. Informe costo-beneficio con figuras y recomendaciones.
