import csv
import os
import numpy as np

DIMENSIONES_TAMAÑO: dict[str, tuple[int, int]] = {
    "A": (8, 10),
    "B": (10, 12),
    "C": (12, 14)
}

FILAS_ZONAS: dict[str, dict[str, tuple[int, int]]] = {
    "A": { 
        "económica": (1, 3),
        "premium": (4, 5),
        "intermedia": (6, 7),
        "última fila": (8, 8)
    },
    "B": {
        "económica": (1, 4),
        "premium": (5, 6),
        "intermedia": (7, 9),
        "última fila": (10, 10)
    },
    "C": {
        "económica": (1, 5),
        "premium": (6, 7),
        "intermedia": (8, 11),
        "última fila": (12, 12)
    }
}

FACTORES_PRECIOS: dict[str, float] = {
    "económica": 1.0,
    "premium": 2.5,
    "intermedia": 1.5,
    "última fila": 1.2
}

SEXOS: tuple[str, ...] = ("hombre", "mujer")


class Sala:
    def __init__(self, nombre: str, tamaño: str, precio_base: float, teatro: str = ""):
        tamaño = tamaño.upper()
        if tamaño not in DIMENSIONES_TAMAÑO:
            raise ValueError("El tamaño debe ser A, B o C")
        if precio_base <= 0:
            raise ValueError("El precio base debe ser mayor que cero")

        self.nombre: str = nombre.strip()
        self.tamaño: str = tamaño
        self.precio_base: float = float(precio_base)
        self.teatro: str = teatro.strip()
        
        self.filas: int = DIMENSIONES_TAMAÑO[tamaño][0]
        self.sillas_por_fila: int = DIMENSIONES_TAMAÑO[tamaño][1]
        
        self.mapa_ocupacion_mensual: np.ndarray | None = None
        self.mapa_ingresos_mensual: np.ndarray | None = None
        self.matriz_ocupacion_dia: np.ndarray | None = None
        self.matriz_demanda_sexo: np.ndarray | None = None


    def validar_asiento(self, fila: int, silla: int) -> bool:
        return 1 <= fila <= self.filas and 1 <= silla <= self.sillas_por_fila

    def zona_de_fila(self, fila: int) -> str:
        zonas = FILAS_ZONAS[self.tamaño]
        for zona, limites in zonas.items():
            fila_inicial, fila_final = limites
            if fila_inicial <= fila <= fila_final:
                return zona
        raise ValueError(f"La fila {fila} no pertenece a ninguna zona")

    def precio_de_silla(self, fila: int) -> float:
        zona = self.zona_de_fila(fila)
        factor = FACTORES_PRECIOS[zona]
        return self.precio_base * factor

    def reiniciar_datos_mensuales(self):
        self.mapa_ocupacion_mensual = None
        self.mapa_ingresos_mensual = None
        self.matriz_ocupacion_dia = None
        self.matriz_demanda_sexo = None

    def convertir_dia(self, fecha: str) -> int:
        fecha = fecha.strip()
        if "-" in fecha:
            partes = fecha.split("-")
            return int(partes[2])
        if "/" in fecha:
            partes = fecha.split("/")
            return int(partes[0])
        raise ValueError(f"Formato de fecha no válido: {fecha}")

    def leer_csv(self, ruta_csv: str) -> list[dict[str, str]]:
        registros: list[dict[str, str]] = []
        try:
            with open(ruta_csv, mode="r", encoding="utf-8", newline="") as archivo:
                lector = csv.DictReader(archivo)
                for fila in lector:

                    coincide_teatro = True if not self.teatro else (fila["teatro"].strip().lower() == self.teatro.lower())
                    if coincide_teatro and fila["sala"].strip().lower() == self.nombre.lower():
                        registros.append(fila)
        except FileNotFoundError:
            raise FileNotFoundError(f"No existe el archivo CSV: {ruta_csv}")

        if len(registros) == 0:
            raise ValueError(f"No existen registros en el CSV para la sala '{self.nombre}'")
        return registros

    def construir_mapa_ocupacion_mensual(self, ruta_csv: str) -> tuple[np.ndarray, list[str]]:
        registros = self.leer_csv(ruta_csv)
        dias = [self.convertir_dia(r["fecha"]) for r in registros]
        cantidad_dias = max(dias)

        mapa = np.zeros((cantidad_dias, self.filas, self.sillas_por_fila), dtype=int)
        advertencias: list[str] = []

        for registro in registros:
            dia = self.convertir_dia(registro["fecha"])
            fila = int(registro["fila"])
            silla = int(registro["silla"])

            if not self.validar_asiento(fila, silla):
                advertencias.append(f"Asiento fuera de rango reportado (fila {fila}, silla {silla}).")
                continue
            
            mapa[dia - 1, fila - 1, silla - 1] += 1

        self.mapa_ocupacion_mensual = mapa
        return mapa, advertencias

    def calcular_estadisticos_ocupacion(self) -> dict:
        if self.mapa_ocupacion_mensual is None:
            raise ValueError("Primero debe construirse el mapa de ocupación mensual.")

        mapa_acumulado_silla = np.sum(self.mapa_ocupacion_mensual, axis=0)

        promedio = round(float(np.mean(mapa_acumulado_silla)), 2)
        desviacion = round(float(np.std(mapa_acumulado_silla)), 2)
        maximo = int(np.max(mapa_acumulado_silla))
        minimo = int(np.min(mapa_acumulado_silla))
        pos_max = np.unravel_index(int(np.argmax(mapa_acumulado_silla)), mapa_acumulado_silla.shape)
        pos_min = np.unravel_index(int(np.argmin(mapa_acumulado_silla)), mapa_acumulado_silla.shape)

        return {
            "promedio": promedio,
            "desviacion_estandar": desviacion,
            "maximo": maximo,
            "minimo": minimo,
            "silla_maxima": (pos_max[0] + 1, pos_max[1] + 1),
            "silla_minima": (pos_min[0] + 1, pos_min[1] + 1)
        }

    def construir_mapa_ingresos_mensual(self) -> np.ndarray:
        if self.mapa_ocupacion_mensual is None:
            raise ValueError("Primero debe construirse el mapa de ocupación mensual.")

        precios = np.zeros((self.filas, self.sillas_por_fila), dtype=float)
        for fila in range(1, self.filas + 1):
            precios[fila - 1, :] = self.precio_de_silla(fila)

        mapa_ocupacion_total_sillas = np.sum(self.mapa_ocupacion_mensual, axis=0)
        mapa_ingresos = mapa_ocupacion_total_sillas * precios

        self.mapa_ingresos_mensual = mapa_ingresos
        return mapa_ingresos

    def analizar_zonas(self) -> dict:
        if self.mapa_ocupacion_mensual is None or self.mapa_ingresos_mensual is None:
            raise ValueError("Debe construir previamente los mapas de ocupación e ingresos.")

        resultados: dict = {}
        mapa_ocupacion_total_sillas = np.sum(self.mapa_ocupacion_mensual, axis=0)

        for zona, limites in FILAS_ZONAS[self.tamaño].items():
            f_in, f_fin = limites

            ocu_zona = mapa_ocupacion_total_sillas[f_in - 1:f_fin, :]
            ing_zona = self.mapa_ingresos_mensual[f_in - 1:f_fin, :]

            cant_sillas = (f_fin - f_in + 1) * self.sillas_por_fila
            ocu_total = int(np.sum(ocu_zona))
            ing_total = float(np.sum(ing_zona))

            resultados[zona] = {
                "ocupacion_total": ocu_total,
                "ocupacion_promedio": round(ocu_total / cant_sillas, 2) if cant_sillas > 0 else 0.0,
                "ingresos_totales": ing_total,
                "ingresos_promedio": round(ing_total / cant_sillas, 2) if cant_sillas > 0 else 0.0
            }

        return resultados

    def construir_matriz_ocupacion_dia(self, ruta_csv: str, dia: int) -> np.ndarray:
        registros = self.leer_csv(ruta_csv)
        registros_dia = [r for r in registros if self.convertir_dia(r["fecha"]) == dia]

        if not registros_dia:
            raise ValueError(f"No existen registros de funciones para el día {dia}.")

        proyecciones = sorted(list(set(r["proyeccion"] for r in registros_dia)))
        pos_proyeccion = {proy: i for i, proy in enumerate(proyecciones)}

        matriz = np.zeros((self.filas, self.sillas_por_fila, len(proyecciones)), dtype=int)

        for r in registros_dia:
            fila = int(r["fila"])
            silla = int(r["silla"])
            if self.validar_asiento(fila, silla):
                idx_p = pos_proyeccion[r["proyeccion"]]
                matriz[fila - 1, silla - 1, idx_p] = 1

        self.matriz_ocupacion_dia = matriz
        return matriz

    def ocupacion_por_proyeccion(self) -> np.ndarray:
        if self.matriz_ocupacion_dia is None:
            raise ValueError("Primero debe construirse la matriz del día.")
        return np.sum(self.matriz_ocupacion_dia, axis=(0, 1))

    def ocupacion_por_silla_en_dia(self) -> np.ndarray:
        if self.matriz_ocupacion_dia is None:
            raise ValueError("Primero debe construirse la matriz del día.")
        return np.sum(self.matriz_ocupacion_dia, axis=2)

    def ocupacion_por_zona_en_dia(self) -> dict[str, int]:
        if self.matriz_ocupacion_dia is None:
            raise ValueError("Primero debe construirse la matriz del día.")

        resultados: dict[str, int] = {}
        for zona, limites in FILAS_ZONAS[self.tamaño].items():
            f_in, f_fin = limites
            submatriz = self.matriz_ocupacion_dia[f_in - 1:f_fin, :, :]
            resultados[zona] = int(np.sum(submatriz))
        return resultados

    def ocupacion_total_por_dia(self) -> np.ndarray:
        if self.mapa_ocupacion_mensual is None:
            raise ValueError("Primero debe construirse el mapa de ocupación mensual.")
        return np.sum(self.mapa_ocupacion_mensual, axis=(1, 2))

    def ocupacion_promedio_por_dia(self) -> np.ndarray:
        if self.mapa_ocupacion_mensual is None:
            raise ValueError("Primero debe construirse el mapa de ocupación mensual.")
        return np.round(np.mean(self.mapa_ocupacion_mensual, axis=(1, 2)), 2)

    def dia_mas_ocupado(self) -> int:
        return int(np.argmax(self.ocupacion_total_por_dia())) + 1

    def dia_menos_ocupado(self) -> int:
        return int(np.argmin(self.ocupacion_total_por_dia())) + 1

    def construir_matriz_demanda_sexo(self, ruta_csv: str) -> np.ndarray:
        registros = self.leer_csv(ruta_csv)
        dias = [self.convertir_dia(r["fecha"]) for r in registros]
        cantidad_dias = max(dias)

        matriz = np.zeros((cantidad_dias, 4, 2), dtype=int)
        pos_sexo = {"hombre": 0, "mujer": 1}
        zonas = ("económica", "premium", "intermedia", "última fila")
        pos_zona = {z: i for i, z in enumerate(zonas)}

        for r in registros:
            dia = self.convertir_dia(r["fecha"])
            fila = int(r["fila"])
            sexo_str = r["sexo"].strip().lower()

            if not self.validar_asiento(fila, 1):
                continue

            sexo = "hombre" if sexo_str in ("m", "masculino", "hombre") else "mujer" if sexo_str in ("f", "femenino", "mujer") else None
            if sexo is None:
                continue

            zona = self.zona_de_fila(fila)
            matriz[dia - 1, pos_zona[zona], pos_sexo[sexo]] += 1

        self.matriz_demanda_sexo = matriz
        return matriz

    def demanda_por_dia(self) -> np.ndarray:
        if self.matriz_demanda_sexo is None:
            raise ValueError("Primero debe construirse la matriz de demanda por sexo.")
        return np.sum(self.matriz_demanda_sexo, axis=(1, 2))

    def demanda_por_zona(self) -> dict[str, int]:
        if self.matriz_demanda_sexo is None:
            raise ValueError("Primero debe construirse la matriz de demanda por sexo.")
        totales = np.sum(self.matriz_demanda_sexo, axis=(0, 2))
        zonas = ("económica", "premium", "intermedia", "última fila")
        return {zona: int(totales[indice]) for indice, zona in enumerate(zonas)}

    def demanda_por_sexo(self) -> dict[str, int]:
        if self.matriz_demanda_sexo is None:
            raise ValueError("Primero debe construirse la matriz de demanda por sexo.")
        totales = np.sum(self.matriz_demanda_sexo, axis=(0, 1))
        return {"hombre": int(totales[0]), "mujer": int(totales[1])}


class Teatro:
    def __init__(self, nombre: str, ciudad: str):
        self.establecer_nombre(nombre)
        self.establecer_ciudad(ciudad)
        self.salas: list[Sala] = []

    def establecer_nombre(self, nombre: str):
        if not isinstance(nombre, str):
            raise TypeError("El nombre del teatro debe ser una cadena de texto.")
        texto_limpio = nombre.strip()
        if not texto_limpio:
            raise ValueError("El nombre del teatro no puede estar vacío.")
        self.nombre = texto_limpio

    def establecer_ciudad(self, ciudad: str):
        if not isinstance(ciudad, str):
            raise TypeError("La ciudad del teatro debe ser una cadena de texto.")
        texto_limpio = ciudad.strip()
        if not texto_limpio:
            raise ValueError("La ciudad del teatro no puede estar vacía.")
        self.ciudad = texto_limpio

    def agregar_sala(self, sala: Sala):
        if not isinstance(sala, Sala):
            raise TypeError("El objeto sala debe ser una instancia de la clase Sala.")
        
        if any(s.nombre.lower() == sala.nombre.lower() for s in self.salas):
            raise ValueError(f"La sala '{sala.nombre}' ya existe en el teatro '{self.nombre}'.")
        
        sala.teatro = self.nombre
        self.salas.append(sala)

    def obtener_sala(self, nombre_sala: str) -> Sala:
        for sala in self.salas:
            if sala.nombre.lower() == nombre_sala.strip().lower():
                return sala
        raise ValueError(f"La sala '{nombre_sala}' no existe en el teatro '{self.nombre}'.")

    def comparar_mapas_ingresos_por_tamaño(self) -> dict:
        grupos: dict[str, list[Sala]] = {}
        for sala in self.salas:
            if sala.mapa_ingresos_mensual is not None:
                grupos.setdefault(sala.tamaño, []).append(sala)

        grupos_validos = {t: ss for t, ss in grupos.items() if len(ss) >= 2}
        if not grupos_validos:
            raise ValueError(
                f"El teatro '{self.nombre}' no tiene al menos dos salas "
                "del mismo tamaño con mapas de ingresos construidos."
            )

        resultados: dict = {}
        for tamaño, salas_grupo in grupos_validos.items():
            cubo = np.stack([s.mapa_ingresos_mensual for s in salas_grupo])
            ingresos_totales = np.sum(cubo, axis=(1, 2))
            idx_max = int(np.argmax(ingresos_totales))
            mapa_promedio = np.round(np.mean(cubo, axis=0), 2)
            diferencias = [np.round(cubo[i] - mapa_promedio, 2) for i in range(len(salas_grupo))]

            resultados[tamaño] = {
                "salas": [s.nombre for s in salas_grupo],
                "ingresos_totales": [float(v) for v in ingresos_totales],
                "sala_mayor_ingreso": salas_grupo[idx_max].nombre,
                "mapa_promedio": mapa_promedio,
                "diferencias": diferencias,
            }
        return resultados

    def calcular_ocupacion_promedio(self) -> float:
        salas_con_mapa = [s for s in self.salas if s.mapa_ocupacion_mensual is not None]
        if not salas_con_mapa:
            raise ValueError(f"El teatro '{self.nombre}' no tiene salas con mapas de ocupación.")
        
        totales = [np.mean(s.mapa_ocupacion_mensual) for s in salas_con_mapa]
        return round(float(np.mean(totales)), 2)

    def calcular_ingreso_promedio(self) -> float:
        salas_con_mapa = [s for s in self.salas if s.mapa_ingresos_mensual is not None]
        if not salas_con_mapa:
            raise ValueError(f"El teatro '{self.nombre}' no tiene salas con mapas de ingresos.")
        
        totales = [np.mean(s.mapa_ingresos_mensual) for s in salas_con_mapa]
        return round(float(np.mean(totales)), 2)    



CAMPOS_ESTRUCTURA = ["teatro", "ciudad", "sala", "tamaño", "precio_base"]


def obtener_texto(valor: str, campo: str) -> str:
    if not isinstance(valor, str):
        raise ValueError(f"El campo '{campo}' debe ser texto.")
    texto_limpio = valor.strip()
    if texto_limpio == "":
        raise ValueError(f"El campo '{campo}' no puede estar vacío.")
    return texto_limpio


def validar_encabezados(lector: csv.DictReader, campos_requeridos: list[str]):
    encabezados = lector.fieldnames
    if encabezados is None:
        raise ValueError("El archivo CSV no tiene encabezados.")
    for campo in campos_requeridos:
        if campo not in encabezados:
            raise ValueError(f"Falta la columna '{campo}' en el archivo CSV.")


class Cinecosta:
    def __init__(self):
        self.teatros: list[Teatro] = []
        self.errores_estructura: list[str] = []
        self.errores_operacion: list[str] = []

    def obtener_teatro(self, nombre: str, ciudad: str = None) -> Teatro | None:
        for teatro in self.teatros:
            if teatro.nombre.lower() == nombre.strip().lower():
                if ciudad is None or teatro.ciudad.lower() == ciudad.strip().lower():
                    return teatro
        return None

    def obtener_sala(self, nombre_teatro: str, nombre_sala: str) -> Sala:
        teatro = self.obtener_teatro(nombre_teatro)
        if teatro is None:
            raise ValueError(f"El teatro '{nombre_teatro}' no existe en la estructura.")
        return teatro.obtener_sala(nombre_sala)

    def cargar_estructura(self, ruta_csv: str) -> int:
        if not os.path.isfile(ruta_csv):
            raise FileNotFoundError(f"No se encontró el archivo de estructura: {ruta_csv}")

        self.teatros = []
        self.errores_estructura = []
        cargadas = 0

        with open(ruta_csv, mode="r", encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            validar_encabezados(lector, CAMPOS_ESTRUCTURA)

            for numero_fila, registro in enumerate(lector, start=2):
                try:
                    nombre_teatro = obtener_texto(registro["teatro"], "teatro")
                    ciudad = obtener_texto(registro["ciudad"], "ciudad")
                    nombre_sala = obtener_texto(registro["sala"], "sala")
                    tamaño = obtener_texto(registro["tamaño"], "tamaño").upper()
                    precio_base = float(obtener_texto(registro["precio_base"], "precio_base"))

                    sala = Sala(nombre_sala, tamaño, precio_base, teatro=nombre_teatro)

                    teatro = self.obtener_teatro(nombre_teatro, ciudad)
                    if teatro is None:
                        teatro = Teatro(nombre_teatro, ciudad)
                        self.teatros.append(teatro)
                    teatro.agregar_sala(sala)
                    cargadas += 1
                except (KeyError, TypeError, ValueError) as error:
                    mensaje = f"Fila {numero_fila}: {error}"
                    self.errores_estructura.append(mensaje)

        if cargadas == 0:
            raise ValueError("El archivo de estructura no tiene registros válidos.")
        return cargadas

    def cargar_operacion_mensual(self, ruta_ventas_csv: str) -> int:
        if len(self.teatros) == 0:
            raise ValueError("Primero debe cargar la estructura de la empresa.")
        if not os.path.isfile(ruta_ventas_csv):
            raise FileNotFoundError(f"No se encontró el archivo de ventas: {ruta_ventas_csv}")

        self.errores_operacion = []
        exitosas = 0

        for teatro in self.teatros:
            for sala in teatro.salas:
                sala.reiniciar_datos_mensuales()
                try:
                    _, advertencias = sala.construir_mapa_ocupacion_mensual(ruta_ventas_csv)
                    for advertencia in advertencias:
                        self.errores_operacion.append(
                            f"Teatro '{teatro.nombre}', sala '{sala.nombre}': {advertencia}"
                        )
                    sala.construir_mapa_ingresos_mensual()
                    exitosas += 1
                except (FileNotFoundError, ValueError) as error:
                    mensaje = f"Teatro '{teatro.nombre}', sala '{sala.nombre}': {error}"
                    self.errores_operacion.append(mensaje)

        return exitosas

    def analizar_sala(self, nombre_teatro: str, nombre_sala: str) -> dict:
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        return {
            "estadisticos_ocupacion": sala.calcular_estadisticos_ocupacion(),
            "mapa_ingresos": sala.mapa_ingresos_mensual,
            "analisis_por_zona": sala.analizar_zonas(),
        }

    def analizar_dia(self, nombre_teatro: str, nombre_sala: str, ruta_ventas_csv: str, dia: int) -> dict:
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        sala.construir_matriz_ocupacion_dia(ruta_ventas_csv, dia)
        return {
            "ocupacion_por_proyeccion": sala.ocupacion_por_proyeccion(),
            "ocupacion_por_silla": sala.ocupacion_por_silla_en_dia(),
            "ocupacion_por_zona": sala.ocupacion_por_zona_en_dia(),
        }

    def analizar_mes(self, nombre_teatro: str, nombre_sala: str) -> dict:
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        if sala.mapa_ocupacion_mensual is None:
            raise ValueError(
                f"La sala '{sala.nombre}' no tiene el mapa de ocupación mensual construido."
            )
        return {
            "ocupacion_total_por_dia": sala.ocupacion_total_por_dia(),
            "ocupacion_promedio_por_dia": sala.ocupacion_promedio_por_dia(),
            "dia_mas_ocupado": sala.dia_mas_ocupado(),
            "dia_menos_ocupado": sala.dia_menos_ocupado(),
        }

    def analizar_demanda_por_sexo(self, nombre_teatro: str, nombre_sala: str, ruta_ventas_csv: str) -> dict:
        sala = self.obtener_sala(nombre_teatro, nombre_sala)
        sala.construir_matriz_demanda_sexo(ruta_ventas_csv)
        return {
            "por_dia": sala.demanda_por_dia(),
            "por_zona": sala.demanda_por_zona(),
            "por_sexo": sala.demanda_por_sexo(),
        }

    def comparar_salas_por_tamaño(self, nombre_teatro: str) -> dict:
        teatro = self.obtener_teatro(nombre_teatro)
        if teatro is None:
            raise ValueError(f"El teatro '{nombre_teatro}' no existe en la estructura.")
        return teatro.comparar_mapas_ingresos_por_tamaño()

    def teatro_de_mejor_desempeño(self) -> dict:
        if len(self.teatros) == 0:
            raise ValueError("La empresa no tiene teatros cargados.")

        resumen: dict[str, dict] = {}
        for teatro in self.teatros:
            mapas_ocupacion = [
                sala.mapa_ocupacion_mensual
                for sala in teatro.salas
                if sala.mapa_ocupacion_mensual is not None
            ]
            mapas_ingresos = [
                sala.mapa_ingresos_mensual
                for sala in teatro.salas
                if sala.mapa_ingresos_mensual is not None
            ]
            if not mapas_ocupacion or not mapas_ingresos:
                continue

            valores_ocupacion = np.concatenate([mapa.flatten() for mapa in mapas_ocupacion])
            valores_ingresos = np.concatenate([mapa.flatten() for mapa in mapas_ingresos])

            resumen[teatro.nombre] = {
                "ocupacion_promedio": round(float(np.mean(valores_ocupacion)), 2),
                "ingreso_promedio": round(float(np.mean(valores_ingresos)), 2),
            }

        if not resumen:
            raise ValueError(
                "Ningún teatro de la empresa tiene mapas de ocupación e ingresos construidos."
            )

        teatro_mayor_ocupacion = max(resumen, key=lambda nombre: resumen[nombre]["ocupacion_promedio"])
        teatro_mayor_ingreso = max(resumen, key=lambda nombre: resumen[nombre]["ingreso_promedio"])

        return {
            "por_teatro": resumen,
            "teatro_mayor_ocupacion_promedio": {
                "teatro": teatro_mayor_ocupacion,
                "valor": resumen[teatro_mayor_ocupacion]["ocupacion_promedio"],
            },
            "teatro_mayor_ingreso_promedio": {
                "teatro": teatro_mayor_ingreso,
                "valor": resumen[teatro_mayor_ingreso]["ingreso_promedio"],
            },
        }       

