import numpy as np
from datetime import date

FILAS_SALA_A = 8
SILLAS_SALA_A = 10
FILAS_SALA_B = 10
SILLAS_SALA_B = 12
FILAS_SALA_C = 12
SILLAS_SALA_C = 14

TAMANOS_VALIDOS = ["A", "B", "C"]

DIMENSIONES_POR_TAMANO = {
    "A": (FILAS_SALA_A, SILLAS_SALA_A),
    "B": (FILAS_SALA_B, SILLAS_SALA_B),
    "C": (FILAS_SALA_C, SILLAS_SALA_C)
}

FACTOR_ECONOMICA = 1.0
FACTOR_PREMIUM = 2.0
FACTOR_INTERMEDIA = 1.5
FACTOR_ULTIMA_FILA = 1.2

ZONA_ECONOMICA = 0
ZONA_PREMIUM = 1
ZONA_INTERMEDIA = 2
ZONA_ULTIMA_FILA = 3
TOTAL_ZONAS = 4

NOMBRE_ZONAS = ["Economica", "Premium", "Intermedia", "Ultima fila"]

ZONAS_POR_TAMANO = {
    "A": {
        ZONA_ECONOMICA: (0, 2),
        ZONA_PREMIUM: (3, 4),
        ZONA_INTERMEDIA: (5, 6),
        ZONA_ULTIMA_FILA: (7, 7)
    },
    "B": {
        ZONA_ECONOMICA: (0, 3),
        ZONA_PREMIUM: (4, 5),
        ZONA_INTERMEDIA: (6, 8),
        ZONA_ULTIMA_FILA: (9, 9)
    },
    "C": {
        ZONA_ECONOMICA: (0, 4),
        ZONA_PREMIUM: (5, 6),
        ZONA_INTERMEDIA: (7, 10),
        ZONA_ULTIMA_FILA: (11, 11)
    }
}


class Sala:

    def __init__(self, nombre, tamano, precio_base):
        self.establecer_nombre(nombre)
        self.establecer_tamaño(tamano)
        self.establecer_precio_base(precio_base)
        self.filas, self.sillas = DIMENSIONES_POR_TAMANO[self.tamano]
        self.zonas = ZONAS_POR_TAMANO[self.tamano]
        self.mapa_precios = self.construir_mapa_precios()
        self.mapa_ocupacion = None
        self.mapa_ingresos = None
        self.matriz_ocupacion_diaria = None
        self.proyecciones_diarias = []
        self.matriz_ocupacion_mensual = None
        self.fechas_mensuales = []
        self.entradas = []

    def establecer_nombre(self, nombre):
        if not isinstance(nombre, str):
            raise TypeError("El nombre de la sala debe ser un texto.")
        if nombre.strip() == "":
            raise ValueError("El nombre de la sala no puede estar vacio.")
        self.nombre = nombre.strip()

    def establecer_tamaño(self, tamano):
        if not isinstance(tamano, str):
            raise TypeError("El tamano de la sala debe ser un texto.")
        tamano = tamano.strip().upper()
        if tamano not in TAMANOS_VALIDOS:
            raise ValueError("El tamano de la sala debe ser A, B o C.")
        self.tamano = tamano

    def establecer_precio_base(self, precio_base):
        if isinstance(precio_base, bool):
            raise TypeError("El precio base debe ser numerico.")
        if not isinstance(precio_base, (int, float)):
            raise TypeError("El precio base debe ser numerico.")
        if not np.isfinite(precio_base) or precio_base <= 0:
            raise ValueError("El precio base debe ser mayor que cero.")
        self.precio_base = float(precio_base)

    def construir_mapa_precios(self):
        mapa = np.zeros((self.filas, self.sillas), dtype=float)
        for zona, limites in self.zonas.items():
            inicio = limites[0]
            fin = limites[1]
            if zona == ZONA_ECONOMICA:
                factor = FACTOR_ECONOMICA
            elif zona == ZONA_PREMIUM:
                factor = FACTOR_PREMIUM
            elif zona == ZONA_INTERMEDIA:
                factor = FACTOR_INTERMEDIA
            else:
                factor = FACTOR_ULTIMA_FILA
            mapa[inicio:fin + 1, :] = self.precio_base * factor
        return mapa

    def zona_de_fila(self, indice_fila):
        for zona, limites in self.zonas.items():
            if limites[0] <= indice_fila <= limites[1]:
                return zona
        raise ValueError("La fila esta fuera del rango de la sala.")

    def verificar_ocupacion_cargada(self):
        if self.mapa_ocupacion is None:
            raise ValueError("Primero debe cargar el mapa de ocupacion.")

    def verificar_ingresos_construidos(self):
        if self.mapa_ingresos is None:
            raise ValueError("Primero debe construir el mapa de ingresos.")

    def reiniciar_datos_mensuales(self):
        self.mapa_ocupacion = None
        self.mapa_ingresos = None
        self.matriz_ocupacion_diaria = None
        self.proyecciones_diarias = []
        self.matriz_ocupacion_mensual = None
        self.fechas_mensuales = []
        self.entradas = []

    def agregar_entrada(self, entrada):
        self.entradas.append(entrada)

    def cargar_mapa_ocupacion(self):
        mapa = np.zeros((self.filas, self.sillas), dtype=int)
        entradas_validas = []
        errores = []

        for entrada in self.entradas:
            try:
                fila = int(entrada["fila"])
                silla = int(entrada["silla"])
            except (KeyError, TypeError, ValueError):
                errores.append("Fila CSV " + str(entrada["numero_fila"]) + ": fila o silla invalidas.")
                continue

            if fila < 1 or fila > self.filas:
                errores.append(
                    "Fila CSV " + str(entrada["numero_fila"]) + ": fila "
                    + str(fila) + " fuera del rango de la sala."
                )
                continue
            if silla < 1 or silla > self.sillas:
                errores.append(
                    "Fila CSV " + str(entrada["numero_fila"]) + ": silla "
                    + str(silla) + " fuera del rango de la sala."
                )
                continue

            mapa[fila - 1, silla - 1] += 1
            entradas_validas.append(entrada)

        self.mapa_ocupacion = mapa
        self.entradas = entradas_validas
        return errores

    def calcular_promedio_ocupacion(self):
        self.verificar_ocupacion_cargada()
        return round(float(np.mean(self.mapa_ocupacion)), 2)

    def calcular_desviacion_estandar_ocupacion(self):
        self.verificar_ocupacion_cargada()
        return round(float(np.std(self.mapa_ocupacion)), 2)

    def obtener_ocupacion_maxima(self):
        self.verificar_ocupacion_cargada()
        indice_maximo = int(np.argmax(self.mapa_ocupacion))
        fila_maxima, silla_maxima = np.unravel_index(
            indice_maximo, self.mapa_ocupacion.shape
        )
        return int(np.max(self.mapa_ocupacion)), (
            int(fila_maxima) + 1, int(silla_maxima) + 1
        )

    def obtener_ocupacion_minima(self):
        self.verificar_ocupacion_cargada()
        indice_minimo = int(np.argmin(self.mapa_ocupacion))
        fila_minima, silla_minima = np.unravel_index(
            indice_minimo, self.mapa_ocupacion.shape
        )
        return int(np.min(self.mapa_ocupacion)), (
            int(fila_minima) + 1, int(silla_minima) + 1
        )

    def calcular_estadisticos_ocupacion(self):
        ocupacion_maxima, posicion_maxima = self.obtener_ocupacion_maxima()
        ocupacion_minima, posicion_minima = self.obtener_ocupacion_minima()

        return {
            "ocupacion_promedio_por_silla": self.calcular_promedio_ocupacion(),
            "desviacion_estandar": self.calcular_desviacion_estandar_ocupacion(),
            "ocupacion_maxima": ocupacion_maxima,
            "posicion_maxima": posicion_maxima,
            "ocupacion_minima": ocupacion_minima,
            "posicion_minima": posicion_minima
        }

    def construir_mapa_ingresos(self):
        self.verificar_ocupacion_cargada()
        self.mapa_ingresos = self.mapa_ocupacion * self.mapa_precios
        return self.mapa_ingresos

    def calcular_ocupacion_total_por_zonas(self):
        self.verificar_ocupacion_cargada()
        resultados = []

        for zona, limites in self.zonas.items():
            inicio = limites[0]
            fin = limites[1]
            ocupacion_zona = self.mapa_ocupacion[inicio:fin + 1, :]
            resultados.append(int(np.sum(ocupacion_zona)))
        return resultados

    def calcular_ocupacion_promedio_por_zonas(self):
        self.verificar_ocupacion_cargada()
        resultados = []

        for zona, limites in self.zonas.items():
            inicio = limites[0]
            fin = limites[1]
            ocupacion_zona = self.mapa_ocupacion[inicio:fin + 1, :]
            resultados.append(round(float(np.mean(ocupacion_zona)), 2))
        return resultados

    def calcular_ingresos_totales_por_zonas(self):
        self.verificar_ingresos_construidos()
        resultados = []

        for zona, limites in self.zonas.items():
            inicio = limites[0]
            fin = limites[1]
            ingresos_zona = self.mapa_ingresos[inicio:fin + 1, :]
            resultados.append(round(float(np.sum(ingresos_zona)), 2))
        return resultados

    def calcular_ingresos_promedio_por_zonas(self):
        self.verificar_ingresos_construidos()
        resultados = []

        for zona, limites in self.zonas.items():
            inicio = limites[0]
            fin = limites[1]
            ingresos_zona = self.mapa_ingresos[inicio:fin + 1, :]
            resultados.append(round(float(np.mean(ingresos_zona)), 2))
        return resultados

    def analizar_por_zona(self):
        ocupaciones_totales = self.calcular_ocupacion_total_por_zonas()
        ocupaciones_promedio = self.calcular_ocupacion_promedio_por_zonas()
        ingresos_totales = self.calcular_ingresos_totales_por_zonas()
        ingresos_promedio = self.calcular_ingresos_promedio_por_zonas()
        resultado = {}

        for zona in range(TOTAL_ZONAS):
            resultado[NOMBRE_ZONAS[zona]] = {
                "ocupacion_total": ocupaciones_totales[zona],
                "ocupacion_promedio_por_silla": ocupaciones_promedio[zona],
                "ingresos_totales": ingresos_totales[zona],
                "ingresos_promedio_por_silla": ingresos_promedio[zona]
            }

        return resultado

    def construir_matriz_dia(self, fecha):
        ventas_dia = []

        for entrada in self.entradas:
            if entrada["fecha"] == fecha:
                ventas_dia.append(entrada)

        if len(ventas_dia) == 0:
            raise ValueError("No hay ventas para la fecha indicada.")

        proyecciones = []
        for entrada in ventas_dia:
            numero = entrada["num_proyeccion"]
            if numero not in proyecciones:
                proyecciones.append(numero)
        proyecciones.sort()

        matriz = np.zeros((len(proyecciones), self.filas, self.sillas), dtype=int)

        for entrada in ventas_dia:
            indice = proyecciones.index(entrada["num_proyeccion"])
            fila = entrada["fila"] - 1
            silla = entrada["silla"] - 1
            matriz[indice, fila, silla] = 1

        self.matriz_ocupacion_diaria = matriz
        self.proyecciones_diarias = proyecciones
        return matriz, proyecciones

    def construir_matriz_mensual(self):
        if len(self.entradas) == 0:
            raise ValueError("No hay ventas para construir la matriz mensual.")

        fechas = []
        for entrada in self.entradas:
            fecha_actual = date.fromisoformat(entrada["fecha"])
            if fecha_actual not in fechas:
                fechas.append(fecha_actual)
        fechas.sort()

        matriz = np.zeros((len(fechas), self.filas, self.sillas), dtype=int)

        for entrada in self.entradas:
            fecha_actual = date.fromisoformat(entrada["fecha"])
            indice = fechas.index(fecha_actual)
            fila = entrada["fila"] - 1
            silla = entrada["silla"] - 1
            matriz[indice, fila, silla] += 1

        self.matriz_ocupacion_mensual = matriz
        self.fechas_mensuales = fechas
        return matriz, fechas

    def verificar_matriz_mensual(self):
        if self.matriz_ocupacion_mensual is None:
            raise ValueError("Primero debe construir la matriz mensual.")

    def calcular_totales_diarios_mes(self):
        self.verificar_matriz_mensual()
        return np.sum(self.matriz_ocupacion_mensual, axis=(1, 2))

    def calcular_promedios_diarios_mes(self):
        totales_diarios = self.calcular_totales_diarios_mes()
        total_sillas = self.filas * self.sillas
        promedios = np.round(totales_diarios / total_sillas, 2)
        return promedios.tolist()

    def obtener_dia_mayor_demanda(self):
        totales_diarios = self.calcular_totales_diarios_mes()
        indice = int(np.argmax(totales_diarios))
        return self.fechas_mensuales[indice]

    def obtener_dia_menor_demanda(self):
        totales_diarios = self.calcular_totales_diarios_mes()
        indice = int(np.argmin(totales_diarios))
        return self.fechas_mensuales[indice]

    def calcular_totales_dia(self, matriz_dia, proyecciones):
        total_por_proyeccion = np.sum(matriz_dia, axis=(1, 2))
        total_por_silla = np.sum(matriz_dia, axis=0)
        total_por_zona = {}

        for zona, limites in self.zonas.items():
            inicio = limites[0]
            fin = limites[1]
            total_por_zona[NOMBRE_ZONAS[zona]] = int(
                np.sum(total_por_silla[inicio:fin + 1, :])
            )

        resultado_proyecciones = {}
        for indice in range(len(proyecciones)):
            resultado_proyecciones[proyecciones[indice]] = int(total_por_proyeccion[indice])

        return {
            "total_sillas_por_proyeccion": resultado_proyecciones,
            "total_ocupaciones_por_silla": total_por_silla,
            "total_sillas_por_zona": total_por_zona
        }
