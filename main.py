"""Punto de entrada: menú de consola del proyecto.

Ejecutar desde la raíz del proyecto:
    python main.py
"""

from pathlib import Path

from src.datos import cargar_campus, cargar_pares_criticos
from src.grafo import Grafo
from src.mst import prim, kruskal, comparar
from src.visualizacion import dibujar_red
from src.flujo import flujo_maximo, corte_minimo
from src.resiliencia import (
    componentes_conexos,
    simular_falla_arista,
    simular_falla_multiples_aristas,
    simular_falla_nodo,
    simular_fallas_aleatorias,
    evaluar_pares,
    proponer_enlaces,
)

DIR_FIGURAS = Path(__file__).resolve().parent / "resultados" / "figuras"

SEPARADOR = "-" * 72


def mostrar_resultado(nombre, resultado, max_pasos=6):
    arbol, pasos = resultado
    print(f"\nPrimeros {min(max_pasos, len(pasos))} pasos de {nombre}:")
    for i, paso in enumerate(pasos[:max_pasos], 1):
        print(f"  {i}. {paso}")
    print("Árbol de expansión mínima:")
    for u, v, peso in arbol:
        print(f"  {u} -- {v} (peso {peso:g})")
    print(f"Peso total: {sum(p for _, _, p in arbol):g}")


def mostrar_comparacion(grafo):
    r = comparar(grafo)
    p, k = r["prim"], r["kruskal"]
    print(f"\n{SEPARADOR}")
    print(f"{'Métrica':<22} | {'Prim':<18} | {'Kruskal':<18} | ¿Coinciden?")
    print(f"{SEPARADOR}")
    print(f"{'Costo total (USD)':<22} | {p['costo']:<18,.0f} | {k['costo']:<18,.0f} | "
          f"{'Sí' if r['mismo_costo'] else 'No'}")
    print(f"{'Tiempo (ms)':<22} | {p['tiempo_ms']:<18.4f} | {k['tiempo_ms']:<18.4f} | N/A")
    print(f"{'Aristas elegidas':<22} | {len(p['arbol']):<18} | {len(k['arbol']):<18} | "
          f"{'Sí' if r['mismas_aristas'] else 'No'}")
    print(f"{SEPARADOR}")


# ---------------------------------------------------------------------------
# Opción 8: Flujo máximo / corte mínimo
# ---------------------------------------------------------------------------

def _listar_nodos(grafo):
    """Imprime la lista de nodos disponibles con su tipo."""
    print("\nNodos disponibles:")
    for v, info in grafo.info.items():
        tipo = info.get("tipo", "?")
        nombre = info.get("nombre", v)
        critico = " [CRÍTICO]" if info.get("critico") else ""
        print(f"  {v:<6}  {tipo:<14}  {nombre}{critico}")


def menu_flujo_maximo(grafo):
    """Opción 8: flujo máximo y corte mínimo entre dos nodos."""
    if not grafo.ady:
        print("Primero carga el dataset (opción 1).")
        return

    _listar_nodos(grafo)

    s = input("\nNodo origen  (source): ").strip().upper()
    t = input("Nodo destino (sink)  : ").strip().upper()

    if s not in grafo.ady:
        print(f"Error: '{s}' no es un nodo válido.")
        return
    if t not in grafo.ady:
        print(f"Error: '{t}' no es un nodo válido.")
        return
    if s == t:
        print("Error: origen y destino deben ser distintos.")
        return

    print(f"\n{SEPARADOR}")
    print(f"  FLUJO MÁXIMO / CORTE MÍNIMO:  {s}  →  {t}")
    print(SEPARADOR)

    valor_flujo, _ = flujo_maximo(grafo, s, t)
    valor_corte, lado_s, aristas_corte = corte_minimo(grafo, s, t)

    print(f"  Nodo de origen       : {s}")
    print(f"  Nodo de destino      : {t}")
    print(f"  Flujo máximo         : {valor_flujo:g} Gbps")
    print(f"  Capacidad del corte  : {valor_corte:g} Gbps")
    print(f"  (Verificación: flujo == corte → "
          f"{'✓ CORRECTO' if abs(valor_flujo - valor_corte) < 1e-6 else '✗ DISCREPANCIA'})")

    print(f"\n  Lado S del corte ({len(lado_s)} nodos): {', '.join(sorted(lado_s))}")
    lado_t = {v for v in grafo.ady if v not in lado_s}
    print(f"  Lado T del corte ({len(lado_t)} nodos): {', '.join(sorted(lado_t))}")

    print(f"\n  Aristas del corte mínimo ({len(aristas_corte)}):")
    if aristas_corte:
        cap_total = 0.0
        for u, v, cap in aristas_corte:
            print(f"    {u} --> {v}  ({cap:g} Gbps)")
            cap_total += cap
        print(f"  Capacidad total del corte: {cap_total:g} Gbps")
    else:
        print("    (ninguna — nodos en el mismo componente sin aristas de corte)")

    print(f"\n  Interpretación:")
    if valor_flujo == 0:
        print("  ✗ No existe ruta entre los nodos seleccionados.")
    else:
        print(f"  La red puede transportar hasta {valor_flujo:g} Gbps entre {s} y {t}.")
        if aristas_corte:
            print(f"  Eliminar las {len(aristas_corte)} aristas del corte mínimo")
            print(f"  desconectaría completamente {s} de {t}.")
            print(f"  Estas son las aristas más vulnerables para este par de nodos.")


# ---------------------------------------------------------------------------
# Opción 9: Simulación de fallas
# ---------------------------------------------------------------------------

def _mostrar_comparativa(original, despues):
    """Muestra una tabla comparativa antes/después de la falla."""
    print(f"\n{'':>4}{'Antes':>18}{'Después':>18}{'Variación':>14}")
    print(f"  {SEPARADOR}")

    def fila(etiq, antes, desp, fmt=":g"):
        var = desp - antes
        signo = "+" if var >= 0 else ""
        print(f"  {etiq:<30} {antes:{fmt[1:]}:>12}  {desp:{fmt[1:]}:>12}  "
              f"{signo}{var:{fmt[1:]}:>10}")

    fila("Nodos en la red", original["nodos"], despues["nodos"], fmt=":.0f")
    fila("Aristas en la red", original["aristas"], despues["aristas"], fmt=":.0f")
    fila("Componentes conexos", original["componentes"], despues["componentes"], fmt=":.0f")

    # Nodos críticos faltantes
    cf_orig = len(original.get("criticos_faltantes", []))
    cf_desp = len(despues.get("criticos_faltantes", []))
    if cf_orig != cf_desp:
        print(f"  {'Nodos críticos perdidos':<30} {cf_orig:>12}  {cf_desp:>12}  "
              f"{'+' if cf_desp - cf_orig >= 0 else ''}{cf_desp - cf_orig:>10}")

    # Pares críticos cubiertos
    fila("Pares críticos cubiertos",
         original["pares_cubiertos"], despues["pares_cubiertos"], fmt=":.0f")

    # Nodos aislados
    aislados_antes = original.get("nodos_aislados", [])
    aislados_despues = despues.get("nodos_aislados", [])
    print(f"\n  Nodos aislados después de la falla: "
          f"{', '.join(aislados_despues) if aislados_despues else 'ninguno'}")
    if despues.get("criticos_faltantes"):
        print(f"  Nodos críticos desaparecidos: "
              f"{', '.join(despues['criticos_faltantes'])}")

    print(f"\n  Detalle de pares críticos:")
    print(f"  {'Par':<14} {'Demanda':>8} {'F.Antes':>8} {'F.Desp.':>8} {'Cubre?':>7}")
    for p_d in despues["pares_flujo"]:
        p_o = next((x for x in original["pares_flujo"]
                    if x["origen"] == p_d["origen"] and x["destino"] == p_d["destino"]), None)
        f_antes = p_o["flujo"] if p_o else 0.0
        f_despues = p_d["flujo"]
        cubre = "✓" if p_d["cubre"] else "✗"
        aislado = " (SIN RUTA)" if p_d.get("aislado") else ""
        print(f"  {p_d['origen']}->{p_d['destino']:<8} "
              f"{p_d['demanda_gbps']:>7.1f}G "
              f"{f_antes:>7.1f}G "
              f"{f_despues:>7.1f}G "
              f"{cubre:>7}{aislado}")


def menu_simulacion_fallas(grafo, pares_criticos):
    """Opción 9: simulación de fallas en la red."""
    if not grafo.ady:
        print("Primero carga el dataset (opción 1).")
        return

    while True:
        print(f"\n{SEPARADOR}")
        print("  SIMULACIÓN DE FALLAS")
        print(SEPARADOR)
        print("  a. Falla de una arista específica")
        print("  b. Falla de múltiples aristas")
        print("  c. Falla de un nodo (y sus conexiones)")
        print("  d. Fallas aleatorias con probabilidad configurable")
        print("  0. Volver al menú principal")
        sub = input("  Opción: ").strip().lower()

        if sub == "0":
            break

        elif sub == "a":
            _listar_nodos(grafo)
            u = input("\n  Nodo u: ").strip().upper()
            v = input("  Nodo v: ").strip().upper()
            original, despues = simular_falla_arista(grafo, pares_criticos, u, v)
            print(f"\n  Simulando falla de la arista {u}--{v}:")
            _mostrar_comparativa(original, despues)

        elif sub == "b":
            _listar_nodos(grafo)
            print("\n  Ingresa aristas a eliminar, una por línea (formato: U V).")
            print("  Línea vacía para terminar.")
            aristas = []
            while True:
                linea = input("  > ").strip().upper()
                if not linea:
                    break
                partes = linea.split()
                if len(partes) != 2:
                    print("  Formato incorrecto. Usa: U V")
                    continue
                aristas.append((partes[0], partes[1]))
            if not aristas:
                print("  No se ingresaron aristas.")
                continue
            original, despues = simular_falla_multiples_aristas(
                grafo, pares_criticos, aristas)
            eliminadas = despues.get("eliminadas", aristas)
            errores = despues.get("errores", [])
            print(f"\n  Simulando falla de {len(eliminadas)} aristas:")
            if errores:
                print(f"  Advertencias: {'; '.join(errores)}")
            _mostrar_comparativa(original, despues)

        elif sub == "c":
            _listar_nodos(grafo)
            nodo = input("\n  Nodo a eliminar: ").strip().upper()
            original, despues = simular_falla_nodo(grafo, pares_criticos, nodo)
            print(f"\n  Simulando falla del nodo '{nodo}' "
                  f"(y sus {len(grafo.ady.get(nodo, {}))} conexiones):")
            _mostrar_comparativa(original, despues)

        elif sub == "d":
            prob_str = input("\n  Probabilidad de falla por arista [0.0 – 1.0]: ").strip()
            semilla_str = input("  Semilla aleatoria (Enter para aleatoria): ").strip()
            prob = float(prob_str)
            semilla = int(semilla_str) if semilla_str else None
            original, despues, eliminadas = simular_fallas_aleatorias(
                grafo, pares_criticos, prob, semilla)
            print(f"\n  Fallas aleatorias (p={prob:.0%}):")
            print(f"  Aristas eliminadas ({len(eliminadas)}): "
                  f"{', '.join(f'{u}-{v}' for u, v in eliminadas) if eliminadas else 'ninguna'}")
            _mostrar_comparativa(original, despues)

        else:
            print("  Opción no reconocida.")


# ---------------------------------------------------------------------------
# Opción 10: Propuesta de redundancia
# ---------------------------------------------------------------------------

def menu_redundancia(grafo, pares_criticos):
    """Opción 10: propuesta de enlaces adicionales para mejorar la resiliencia."""
    if not grafo.ady:
        print("Primero carga el dataset (opción 1).")
        return

    print(f"\n{SEPARADOR}")
    print("  PROPUESTA DE REDUNDANCIA")
    print(SEPARADOR)

    # Calcular el MST con Kruskal
    arbol_mst, _ = kruskal(grafo)
    costo_mst = sum(p for _, _, p in arbol_mst)
    n_aristas_mst = len(arbol_mst)

    print(f"\n  MST calculado (Kruskal):")
    print(f"    Aristas en el MST : {n_aristas_mst}")
    print(f"    Costo del MST     : USD {costo_mst:,.0f}")
    print(f"\n  Evaluando pares críticos sobre el MST...")

    # Evaluar pares críticos en el MST
    grafo_mst = grafo.subgrafo_con_aristas(arbol_mst)
    pares_mst = evaluar_pares(grafo_mst, pares_criticos)
    cubren_mst = sum(1 for p in pares_mst if p["cubre_demanda"])
    print(f"  Pares críticos cubiertos por el MST: {cubren_mst}/{len(pares_criticos)}")

    top_str = input("\n  ¿Cuántas propuestas mostrar? [por defecto 5]: ").strip()
    top_n = int(top_str) if top_str.isdigit() and int(top_str) > 0 else 5

    print(f"\n  Calculando mejores {top_n} conexiones adicionales...")
    propuestas = proponer_enlaces(grafo, arbol_mst, pares_criticos, top_n=top_n)

    if not propuestas:
        print("  No se encontraron aristas candidatas con capacidad > 0.")
        return

    print(f"\n{SEPARADOR}")
    print(f"  RANKING DE CONEXIONES ADICIONALES (por razón beneficio/costo)")
    print(SEPARADOR)

    for i, prop in enumerate(propuestas, 1):
        u, v = prop["u"], prop["v"]
        cap = prop["capacidad_gbps"]
        costo_e = prop["costo_enlace_usd"]
        costo_tot = prop["costo_total_usd"]
        mejora = prop["mejora_flujo_gbps"]
        razon = prop["razon_beneficio_costo"]
        d_corte = prop["delta_corte_gbps"]
        corte_b = prop["corte_base_gbps"]
        corte_n = prop["corte_nuevo_gbps"]

        mejora_pct = (mejora / max(sum(p["demanda_gbps"] for p in pares_criticos), 1)) * 100

        print(f"\n  [{i}] {u} ── {v}  ({cap:g} Gbps)")
        print(f"       Costo del enlace          : USD {costo_e:>12,.0f}")
        print(f"       Costo total (MST + enlace) : USD {costo_tot:>12,.0f}")
        print(f"       Mejora de flujo total      : {mejora:>8.2f} Gbps  ({mejora_pct:.1f}% de demanda total)")
        print(f"       Razón beneficio/costo      : {razon:.6f} Gbps/USD")
        if corte_b > 0 or corte_n > 0:
            print(f"       Corte mínimo (par ref.)   : {corte_b:.1f} → {corte_n:.1f} Gbps  "
                  f"(Δ {d_corte:+.1f} Gbps)")
        print(f"       Detalle por par crítico:")
        for dp in prop["detalle_pares"]:
            if dp["delta"] > 0:
                pct_inc = (dp["delta"] / max(dp["flujo_base"], 1e-9)) * 100
                print(f"         {dp['par']:<14} "
                      f"{dp['flujo_base']:.1f} → {dp['flujo_nuevo']:.1f} Gbps  "
                      f"(+{dp['delta']:.1f} Gbps, +{pct_inc:.0f}%)")

    # Resumen de recomendación
    mejor = propuestas[0]
    print(f"\n{SEPARADOR}")
    print(f"  RECOMENDACIÓN:")
    print(f"  La mejor conexión adicional es {mejor['u']}──{mejor['v']}:")
    print(f"  - Costo de instalación   : USD {mejor['costo_enlace_usd']:,.0f}")
    print(f"  - Mejora de flujo        : +{mejor['mejora_flujo_gbps']:.2f} Gbps")
    print(f"  - Razón benef./costo     : {mejor['razon_beneficio_costo']:.6f} Gbps/USD")
    print(f"  Esta conexión proporciona la mayor mejora de resiliencia por unidad de costo.")
    print(SEPARADOR)


# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------

def menu():
    grafo = Grafo()
    pares_criticos = []

    while True:
        print("\n=== RED DEL CAMPUS: MST Y RESILIENCIA ===")
        print("1. Cargar dataset del campus")
        print("2. Mostrar grafo")
        print("3. MST por Prim")
        print("4. MST por Kruskal")
        print("5. Comparar Prim vs Kruskal")
        print("6. Guardar figura de la red y su MST")
        print("7. Ver pares críticos")
        print("8. Flujo máximo / corte mínimo")
        print("9. Simulación de fallas")
        print("10. Propuesta de redundancia")
        print("0. Salir")
        opcion = input("Opción: ").strip()

        try:
            if opcion == "1":
                grafo = cargar_campus()
                pares_criticos = cargar_pares_criticos()
                print(f"Campus cargado: {len(grafo.ady)} nodos, "
                      f"{len(grafo.aristas())} enlaces candidatos, "
                      f"costo de construir todos: USD {grafo.costo_total():,.0f}")
                print(f"Pares críticos cargados: {len(pares_criticos)}")
            elif opcion == "2":
                grafo.mostrar()
            elif opcion == "3":
                mostrar_resultado("Prim", prim(grafo))
            elif opcion == "4":
                mostrar_resultado("Kruskal", kruskal(grafo))
            elif opcion == "5":
                mostrar_comparacion(grafo)
            elif opcion == "6":
                arbol, _ = kruskal(grafo)
                DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
                archivo = DIR_FIGURAS / "campus_mst.png"
                dibujar_red(grafo, resaltar=arbol,
                            titulo="Campus: enlaces candidatos y MST", archivo=archivo)
                print(f"Figura guardada en {archivo}")
            elif opcion == "7":
                if not pares_criticos:
                    pares_criticos = cargar_pares_criticos()
                for p in pares_criticos:
                    print(f"  {p['origen']} -> {p['destino']}: {p['demanda_gbps']:g} Gbps "
                          f"[{p['prioridad']}] {p['justificacion']}")
            elif opcion == "8":
                menu_flujo_maximo(grafo)
            elif opcion == "9":
                if not pares_criticos:
                    pares_criticos = cargar_pares_criticos()
                menu_simulacion_fallas(grafo, pares_criticos)
            elif opcion == "10":
                if not pares_criticos:
                    pares_criticos = cargar_pares_criticos()
                menu_redundancia(grafo, pares_criticos)
            elif opcion == "0":
                break
            else:
                print("Opción no válida.")
        except (ValueError, OverflowError, NotImplementedError) as error:
            print(f"Error: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    menu()
