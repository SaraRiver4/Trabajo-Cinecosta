from typing import Optional
from logica_cinecosta import Cinecosta, Teatro, Sala

def pedir_ruta(mensaje: str) -> str:
    return input(mensaje).strip()


def elegir_teatro(empresa: Cinecosta) -> Optional[Teatro]:
    if not empresa.teatros:
        print("No hay teatros cargados todavía. Use primero la opción 1 del menú.")
        return None

    print("\nTeatros disponibles:")
    for i, teatro in enumerate(empresa.teatros, start=1):
        print(f"  {i}. {teatro.nombre} ({teatro.ciudad})")

    seleccion = input("Seleccione el número del teatro: ").strip()
    try:
        idx = int(seleccion) - 1
        if idx < 0 or idx >= len(empresa.teatros):
            raise ValueError
    except ValueError:
        print("Selección inválida.")
        return None

    return empresa.teatros[idx]


def elegir_sala(teatro: Teatro) -> Optional[Sala]:
    if not teatro.salas:
        print(f"El teatro '{teatro.nombre}' no tiene salas registradas.")
        return None

    print(f"\nSalas de {teatro.nombre}:")
    for i, sala in enumerate(teatro.salas, start=1):
        print(f"  {i}. {sala.nombre} (tipo {sala.tamaño}, precio base ${sala.precio_base:,.2f})")

    seleccion = input("Seleccione el número de la sala: ").strip()
    try:
        idx = int(seleccion) - 1
        if idx < 0 or idx >= len(teatro.salas):
            raise ValueError
    except ValueError:
        print("Selección inválida.")
        return None

    return teatro.salas[idx]


def mostrar_errores(errores: list) -> None:
    if errores:
        print(f"\nSe encontraron {len(errores)} registro(s) con problemas/advertencias:")
        for e in errores[:20]:
            print(f"  - {e}")
        if len(errores) > 20:
            print(f"  ... y {len(errores) - 20} más.")


def opcion_01_cargar_estructura(empresa: Cinecosta) -> None:
    print("\n=== Cargar estructura de la empresa (teatros y salas) ===")
    ruta = pedir_ruta("Ruta del archivo CSV de teatros/salas: ")
    try:
        cargadas = empresa.cargar_estructura(ruta)
        print(f"\nSalas cargadas correctamente: {cargadas}")
        print(f"Teatros registrados: {len(empresa.teatros)}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")

    mostrar_errores(empresa.errores_estructura)


def opcion_02_cargar_ventas(empresa: Cinecosta) -> None:
    print("\n=== Cargar entradas vendidas (construye el mapa de ocupación e ingresos) ===")
    ruta = pedir_ruta("Ruta del archivo CSV de ventas del mes: ")
    try:
        exitosas = empresa.cargar_operacion_mensual(ruta)
        print(f"\nSalas procesadas correctamente: {exitosas}")
        print("\nEl mapa de ocupación e ingresos quedó actualizado para las salas.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")

    mostrar_errores(empresa.errores_operacion)


def opcion_03_estadisticas_ocupacion(empresa: Cinecosta) -> None:
    print("\n=== Estadísticas de ocupación de una sala ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return
    sala = elegir_sala(teatro)
    if sala is None:
        return

    try:
        stats = sala.calcular_estadisticos_ocupacion()
        print(f"\nSala: {sala.nombre}  (Teatro: {teatro.nombre})")
        print(f"  Ocupación promedio por silla: {stats['promedio']}")
        print(f"  Desviación estándar: {stats['desviacion_estandar']}")
        print(f"  Silla más demandada: fila {stats['silla_maxima'][0]}, silla {stats['silla_maxima'][1]} con {stats['maximo']} ocupaciones")
        print(f"  Silla menos demandada: fila {stats['silla_minima'][0]}, silla {stats['silla_minima'][1]} con {stats['minimo']} ocupaciones")
    except ValueError as e:
        print(f"Error: {e}")



def opcion_04_mapa_ingresos(empresa: Cinecosta) -> None:
    print("\n=== Construir/Consultar mapa de ingresos de una sala ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return
    sala = elegir_sala(teatro)
    if sala is None:
        return

    try:
        if sala.mapa_ingresos_mensual is None:
            sala.construir_mapa_ingresos_mensual()

        total = float(sala.mapa_ingresos_mensual.sum())
        print(f"\nMapa de ingresos disponible para '{sala.nombre}'.")
        print(f"Ingresos totales del mes en esta sala: ${total:,.2f}")
    except ValueError as e:
        print(f"Error: {e}")



def opcion_05_estadisticas_por_zona(empresa: Cinecosta) -> None:
    print("\n=== Estadísticas por zona de una sala ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return
    sala = elegir_sala(teatro)
    if sala is None:
        return

    try:
        resultados = sala.analizar_zonas()
        print(f"\nSala: {sala.nombre}  (Teatro: {teatro.nombre})")
        for zona, datos in resultados.items():
            print(f"\n  Zona {zona}:")
            print(f"    Ocupación total: {datos['ocupacion_total']}")
            print(f"    Ocupación promedio por silla: {datos['ocupacion_promedio']}")
            print(f"    Ingresos totales: ${datos['ingresos_totales']:,.2f}")
            print(f"    Ingresos promedio por silla: ${datos['ingresos_promedio']:,.2f}")
    except ValueError as e:
        print(f"Error: {e}")



def opcion_06_analisis_dia(empresa: Cinecosta) -> None:
    print("\n=== Análisis de un día específico ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return
    sala = elegir_sala(teatro)
    if sala is None:
        return

    ruta = pedir_ruta("Ruta del archivo CSV de ventas del mes: ")
    try:
        dia = int(input("Número del día a analizar (ej. 15): ").strip())
        res = empresa.analizar_dia(teatro.nombre, sala.nombre, ruta, dia)

        print(f"\nDía {dia} — Sala {sala.nombre}")
        print(f"  Sillas ocupadas por proyección: {res['ocupacion_por_proyeccion']}")
        print("  Sillas ocupadas por zona ese día:")
        for zona, total in res['ocupacion_por_zona'].items():
            print(f"    {zona}: {total}")
    except ValueError as e:
        print(f"Error: {e}")



def opcion_07_analisis_mensual(empresa: Cinecosta) -> None:
    print("\n=== Análisis mensual día a día ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return
    sala = elegir_sala(teatro)
    if sala is None:
        return

    try:
        stats = empresa.analizar_mes(teatro.nombre, sala.nombre)

        print(f"\nResumen mensual — Sala {sala.nombre}")
        print("\n  Ocupación total por día (índice = día-1):")
        print(f"    {stats['ocupacion_total_por_dia']}")

        print("\n  Ocupación promedio por silla por día:")
        print(f"    {stats['ocupacion_promedio_por_dia']}")

        print(f"\n  Día más ocupado: Día {stats['dia_mas_ocupado']}")
        print(f"  Día menos ocupado: Día {stats['dia_menos_ocupado']}")
    except ValueError as e:
        print(f"Error: {e}")



def opcion_08_demanda_sexo(empresa: Cinecosta) -> None:
    print("\n=== Demanda por sexo (por día y por zona) ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return
    sala = elegir_sala(teatro)
    if sala is None:
        return

    ruta = pedir_ruta("Ruta del archivo CSV de ventas del mes: ")
    try:
        consulta = empresa.analizar_demanda_por_sexo(teatro.nombre, sala.nombre, ruta)

        print(f"\nDemanda por sexo — Sala {sala.nombre}:")
        print(f"  Totales generales: Hombres={consulta['por_sexo']['hombre']}, Mujeres={consulta['por_sexo']['mujer']}")

        print("\nDemanda por zona:")
        for zona, total in consulta["por_zona"].items():
            print(f"  {zona}: {total} asistentes")

    except ValueError as e:
        print(f"Error: {e}")



def opcion_09_comparar_salas(empresa: Cinecosta) -> None:
    print("\n=== Comparar salas del mismo tamaño dentro de un teatro ===")
    teatro = elegir_teatro(empresa)
    if teatro is None:
        return

    try:
        resultado = empresa.comparar_salas_por_tamaño(teatro.nombre)
        print(f"\nComparación realizada para el teatro '{teatro.nombre}':")
        for tamaño, datos in resultado.items():
            print(f"\n  Salas de Tamaño {tamaño}: {datos['salas']}")
            print("  Ingresos totales por sala:")
            for nombre_sala, total in zip(datos['salas'], datos['ingresos_totales']):
                print(f"    - {nombre_sala}: ${total:,.2f}")
            print(f"  Sala con mayor ingreso: {datos['sala_mayor_ingreso']}")
            print("  Mapa de ingresos promedio entre salas de esta categoría:")
            print(datos['mapa_promedio'])
    except ValueError as e:
        print(f"Error: {e}")



def opcion_10_comparar_teatros(empresa: Cinecosta) -> None:
    print("\n=== Comparar teatros (ocupación e ingreso promedio) ===")

    try:
        resultado = empresa.teatro_de_mejor_desempeño()

        print("\nResultados por teatro:")
        for nombre, datos in resultado["por_teatro"].items():
            print(f"  {nombre}: ocupación promedio = {datos['ocupacion_promedio']}, "
                  f"ingreso promedio = ${datos['ingreso_promedio']:,.2f}")

        mayor_ocu = resultado["teatro_mayor_ocupacion_promedio"]
        mayor_ing = resultado["teatro_mayor_ingreso_promedio"]

        print(f"\nTeatro con mayor ocupación promedio: {mayor_ocu['teatro']} ({mayor_ocu['valor']})")
        print(f"Teatro con mayor ingreso promedio: {mayor_ing['teatro']} (${mayor_ing['valor']:,.2f})")
    except ValueError as e:
        print(f"Error: {e}")



OPCIONES = {
    "1": ("Cargar estructura de la empresa (teatros y salas)", opcion_01_cargar_estructura),
    "2": ("Cargar entradas vendidas del mes (mapa de ocupación)", opcion_02_cargar_ventas),
    "3": ("Estadísticas de ocupación de una sala", opcion_03_estadisticas_ocupacion),
    "4": ("Construir mapa de ingresos de una sala", opcion_04_mapa_ingresos),
    "5": ("Estadísticas por zona de una sala", opcion_05_estadisticas_por_zona),
    "6": ("Análisis de un día específico", opcion_06_analisis_dia),
    "7": ("Análisis mensual día a día", opcion_07_analisis_mensual),
    "8": ("Demanda por sexo (día/zona)", opcion_08_demanda_sexo),
    "9": ("Comparar salas del mismo tamaño", opcion_09_comparar_salas),
    "10": ("Comparar teatros", opcion_10_comparar_teatros),
}


def mostrar_menu() -> None:
    print("\n" + "=" * 60)
    print("  CINECOSTA — Panel de análisis de operaciones")
    print("=" * 60)
    for clave, (descripcion, _) in OPCIONES.items():
        print(f"  {clave}. {descripcion}")
    print("  0. Salir")


def main() -> None:
    empresa = Cinecosta()

    while True:
        mostrar_menu()
        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            print("Hasta luego.")
            break

        accion = OPCIONES.get(opcion)
        if accion is None:
            print("Opción no válida. Intente de nuevo.")
            continue

        _, funcion = accion
        try:
            funcion(empresa)
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    main()