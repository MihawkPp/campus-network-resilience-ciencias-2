"""Punto de entrada: menú de consola del proyecto.

Ejecutar desde la raíz del proyecto:
    python main.py
"""

from pathlib import Path

from src.datos import cargar_campus, cargar_pares_criticos
from src.grafo import Grafo
from src.mst import prim, kruskal, comparar
from src.visualizacion import dibujar_red

DIR_FIGURAS = Path(__file__).resolve().parent / "resultados" / "figuras"


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
    print(f"\n{'-' * 72}")
    print(f"{'Métrica':<22} | {'Prim':<18} | {'Kruskal':<18} | ¿Coinciden?")
    print(f"{'-' * 72}")
    print(f"{'Costo total (USD)':<22} | {p['costo']:<18,.0f} | {k['costo']:<18,.0f} | "
          f"{'Sí' if r['mismo_costo'] else 'No'}")
    print(f"{'Tiempo (ms)':<22} | {p['tiempo_ms']:<18.4f} | {k['tiempo_ms']:<18.4f} | N/A")
    print(f"{'Aristas elegidas':<22} | {len(p['arbol']):<18} | {len(k['arbol']):<18} | "
          f"{'Sí' if r['mismas_aristas'] else 'No'}")
    print(f"{'-' * 72}")


def menu():
    grafo = Grafo()
    while True:
        print("\n=== RED DEL CAMPUS: MST Y RESILIENCIA ===")
        print("1. Cargar dataset del campus")
        print("2. Mostrar grafo")
        print("3. MST por Prim")
        print("4. MST por Kruskal")
        print("5. Comparar Prim vs Kruskal")
        print("6. Guardar figura de la red y su MST")
        print("7. Ver pares críticos")
        print("8. Flujo máximo / corte mínimo   (por implementar)")
        print("9. Simulación de fallas           (por implementar)")
        print("10. Propuesta de redundancia      (por implementar)")
        print("0. Salir")
        opcion = input("Opción: ").strip()

        try:
            if opcion == "1":
                grafo = cargar_campus()
                print(f"Campus cargado: {len(grafo.ady)} nodos, "
                      f"{len(grafo.aristas())} enlaces candidatos, "
                      f"costo de construir todos: USD {grafo.costo_total():,.0f}")
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
                for p in cargar_pares_criticos():
                    print(f"  {p['origen']} -> {p['destino']}: {p['demanda_gbps']:g} Gbps "
                          f"[{p['prioridad']}] {p['justificacion']}")
            elif opcion in ("8", "9", "10"):
                print("Pendiente: ver src/flujo.py y src/resiliencia.py")
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
