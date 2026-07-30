import csv
from datetime import date

from clase_sala import Sala
from clase_teatro import Teatro

CAMPOS_ESTRUCTURA = ["teatro", "ciudad", "sala", "tamano", "precio_base"]
CAMPOS_VENTAS = [
    "teatro", "sala", "fecha", "num_proyeccion", "hora_inicio",
    "fila", "silla", "edad", "sexo"
]


def obtener_texto(valor, campo):
    if not isinstance(valor, str):
        raise ValueError("El campo '" + campo + "' debe ser texto.")
    if valor.strip() == "":
        raise ValueError("El campo '" + campo + "' no puede estar vacio.")
    return valor.strip()


def validar_encabezados(lector, campos_requeridos):
    encabezados = lector.fieldnames
    if encabezados is None:
        raise ValueError("El archivo CSV no tiene encabezados.")
    for campo in campos_requeridos:
        if campo not in encabezados:
            raise ValueError("Falta la columna '" + campo + "' en el archivo CSV.")


def fecha_valida(fecha):
    try:
        date.fromisoformat(fecha)
    except ValueError:
        return False
    return True


class Cinecosta:

    def __init__(self):
        self.teatros = []
        self.errores_estructura = []
        self.errores_ventas = []

    def obtener_teatro(self, nombre, ciudad):
        for teatro in self.teatros:
            if teatro.nombre.lower() == nombre.strip().lower():
                if ciudad is None or teatro.ciudad.lower() == ciudad.strip().lower():
                    return teatro
        return None

    def obtener_sala(self, nombre_teatro, nombre_sala):
        teatro = self.obtener_teatro(nombre_teatro, None)
        if teatro is None:
            raise ValueError("El teatro no existe en la estructura.")
        sala = teatro.obtener_sala(nombre_sala)
        if sala is None:
            raise ValueError("La sala no existe en el teatro indicado.")
        return sala

    def cargar_estructura(self, ruta_csv):
        try:
            archivo = open(ruta_csv, "r", encoding="utf-8-sig", newline="")
        except OSError:
            raise FileNotFoundError("No se encontro el archivo de estructura.")

        self.teatros = []
        self.errores_estructura = []
        cargados = 0

        with archivo:
            lector = csv.DictReader(archivo)
            validar_encabezados(lector, CAMPOS_ESTRUCTURA)

            for numero_fila, registro in enumerate(lector, start=2):
                try:
                    nombre_teatro = obtener_texto(registro["teatro"], "teatro")
                    ciudad = obtener_texto(registro["ciudad"], "ciudad")
                    nombre_sala = obtener_texto(registro["sala"], "sala")
                    tamano = obtener_texto(registro["tamano"], "tamano").upper()
                    precio_base = float(obtener_texto(registro["precio_base"], "precio_base"))
                    sala = Sala(nombre_sala, tamano, precio_base)

                    teatro = self.obtener_teatro(nombre_teatro, ciudad)
                    if teatro is None:
                        teatro = Teatro(nombre_teatro, ciudad)
                        self.teatros.append(teatro)
                    teatro.agregar_sala(sala)
                    cargados += 1
                except (KeyError, TypeError, ValueError) as error:
                    mensaje = "Fila " + str(numero_fila) + ": " + str(error)
                    self.errores_estructura.append(mensaje)
                    print(mensaje)

        if cargados == 0:
            raise ValueError("El archivo de estructura no tiene registros validos.")
        return cargados

    def cargar_ventas_mensuales(self, ruta_csv):
        if len(self.teatros) == 0:
            raise ValueError("Primero debe cargar la estructura de la empresa.")

        try:
            archivo = open(ruta_csv, "r", encoding="utf-8-sig", newline="")
        except OSError:
            raise FileNotFoundError("No se encontro el archivo de ventas.")

        self.errores_ventas = []
        for teatro in self.teatros:
            for sala in teatro.salas:
                sala.reiniciar_datos_mensuales()

        cargadas = 0

        with archivo:
            lector = csv.DictReader(archivo)
            validar_encabezados(lector, CAMPOS_VENTAS)

            for numero_fila, registro in enumerate(lector, start=2):
                try:
                    nombre_teatro = obtener_texto(registro["teatro"], "teatro")
                    nombre_sala = obtener_texto(registro["sala"], "sala")
                    fecha = obtener_texto(registro["fecha"], "fecha")
                    num_proyeccion = int(obtener_texto(registro["num_proyeccion"], "num_proyeccion"))
                    hora_inicio = obtener_texto(registro["hora_inicio"], "hora_inicio")
                    fila = int(obtener_texto(registro["fila"], "fila"))
                    silla = int(obtener_texto(registro["silla"], "silla"))
                    edad = int(obtener_texto(registro["edad"], "edad"))
                    sexo = obtener_texto(registro["sexo"], "sexo").upper()

                    if not fecha_valida(fecha):
                        raise ValueError("La fecha no tiene formato AAAA-MM-DD.")
                    if num_proyeccion <= 0:
                        raise ValueError("El numero de proyeccion debe ser mayor que cero.")
                    if edad < 0:
                        raise ValueError("La edad no puede ser negativa.")

                    sala = self.obtener_sala(nombre_teatro, nombre_sala)
                    entrada = {
                        "numero_fila": numero_fila,
                        "fecha": fecha,
                        "num_proyeccion": num_proyeccion,
                        "hora_inicio": hora_inicio,
                        "fila": fila,
                        "silla": silla,
                        "edad": edad,
                        "sexo": sexo
                    }
                    sala.agregar_entrada(entrada)
                    cargadas += 1
                except (KeyError, TypeError, ValueError) as error:
                    mensaje = "Fila " + str(numero_fila) + ": " + str(error)
                    self.errores_ventas.append(mensaje)
                    print(mensaje)

        errores_asientos = []
        for teatro in self.teatros:
            for sala in teatro.salas:
                errores_sala = sala.cargar_mapa_ocupacion()
                for error in errores_sala:
                    mensaje = "Sala " + sala.nombre + ": " + error
                    errores_asientos.append(mensaje)
                    print(mensaje)
                sala.construir_mapa_ingresos()

        self.errores_ventas.extend(errores_asientos)
        return cargadas - len(errores_asientos)

    def analizar_sala(self, nombre_teatro, nombre_sala):
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        sala.construir_mapa_ingresos()
        return {
            "estadisticas_ocupacion": sala.calcular_estadisticos_ocupacion(),
            "mapa_ingresos": sala.mapa_ingresos,
            "analisis_por_zona": sala.analizar_por_zona()
        }

    def analizar_dia(self, nombre_teatro, nombre_sala, fecha):
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        matriz, proyecciones = sala.construir_matriz_dia(fecha)
        return {
            "matriz_ocupacion_diaria": matriz,
            "proyecciones": proyecciones,
            "analisis": sala.calcular_totales_dia(matriz, proyecciones)
        }

    def analizar_mes(self, nombre_teatro, nombre_sala):
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        matriz, fechas = sala.construir_matriz_mensual()
        return {
            "matriz_ocupacion_mensual": matriz,
            "fechas": fechas,
            "totales_diarios": sala.calcular_totales_diarios_mes(),
            "promedios_diarios": sala.calcular_promedios_diarios_mes(),
            "dia_mayor_demanda": sala.obtener_dia_mayor_demanda(),
            "dia_menor_demanda": sala.obtener_dia_menor_demanda()
        }

    def analizar_demanda_sexo(self, nombre_teatro, nombre_sala):
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        matriz, fechas = sala.construir_matriz_demanda_sexo()
        return {
            "matriz_demanda_sexo": matriz,
            "fechas": fechas,
            "totales_por_zona_y_sexo": sala.calcular_totales_por_zona_y_sexo(),
            "totales_por_dia_y_sexo": sala.calcular_totales_por_dia_y_sexo(),
            "totales_por_dia_y_zona": sala.calcular_totales_por_dia_y_zona(),
            "sexo_dominante": sala.obtener_sexo_dominante_del_mes()
        }
