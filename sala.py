import csv
import numpy as np


FILAS_SALA_A:  int = 8
SILLAS_SALA_A: int = 10
FILAS_SALA_B:  int = 10
SILLAS_SALA_B: int = 12
FILAS_SALA_C:  int = 12
SILLAS_SALA_C: int = 14

TAMAÑOS_VALIDOS: list[str] = ["A", "B", "C"]

DIMENSIONES_POR_TAMAÑO: dict[str, tuple[int, int]] = {
    "A": (FILAS_SALA_A,  SILLAS_SALA_A),
    "B": (FILAS_SALA_B,  SILLAS_SALA_B),
    "C": (FILAS_SALA_C,  SILLAS_SALA_C),
}


FACTOR_PREMIUM:     float = 1.8
FACTOR_INTERMEDIA:  float = 1.3
FACTOR_ULTIMA_FILA: float = 1.2


ZONA_ECONOMICA:   int = 0
ZONA_PREMIUM:     int = 1
ZONA_INTERMEDIA:  int = 2
ZONA_ULTIMA_FILA: int = 3
TOTAL_ZONAS:      int = 4

NOMBRE_ZONAS: list[str] = ["Económica", "Premium", "Intermedia", "Última fila"]

ZONAS_POR_TAMAÑO: dict[str, dict[int, tuple[int, int]]] = {
    "A": {
        ZONA_ECONOMICA:   (0, 2),
        ZONA_PREMIUM:     (3, 4),
        ZONA_INTERMEDIA:  (5, 6),
        ZONA_ULTIMA_FILA: (7, 7),
    },
    "B": {
        ZONA_ECONOMICA:   (0, 3),
        ZONA_PREMIUM:     (4, 5),
        ZONA_INTERMEDIA:  (6, 8),
        ZONA_ULTIMA_FILA: (9, 9),
    },
    "C": {
        ZONA_ECONOMICA:   (0, 4),
        ZONA_PREMIUM:     (5, 6),
        ZONA_INTERMEDIA:  (7, 10),
        ZONA_ULTIMA_FILA: (11, 11),
    },
}


SEXO_M:        int       = 0
SEXO_F:        int       = 1
TOTAL_SEXOS:   int       = 2
SEXOS_VALIDOS: list[str] = ["M", "F"]


class Sala:

    def __init__(self, nombre: str, tamaño: str, precio_base: float):
        self._establecer_nombre(nombre)
        self._establecer_tamaño(tamaño)
        self._establecer_precio_base(precio_base)
        filas, sillas       = DIMENSIONES_POR_TAMAÑO[self.tamaño]
        self.filas:  int    = filas
        self.sillas: int    = sillas
        self.zonas:  dict   = ZONAS_POR_TAMAÑO[self.tamaño]
        self.mapa_precios:   np.ndarray        = self._construir_mapa_precios()
        self.mapa_ocupacion: np.ndarray | None = None
        self.mapa_ingresos:  np.ndarray | None = None
        self._entradas:      list[dict]        = []


    def _establecer_nombre(self, nombre: str):
        if not isinstance(nombre, str):
            raise TypeError("El nombre de la sala debe ser de tipo str.")
        texto_limpio = nombre.strip()
        if texto_limpio == "":
            raise ValueError("El nombre de la sala no puede estar vacío.")
        self.nombre = texto_limpio

    def _establecer_tamaño(self, tamaño: str):
        if not isinstance(tamaño, str):
            raise TypeError("El tamaño de la sala debe ser de tipo str.")
        if tamaño not in TAMAÑOS_VALIDOS:
            raise ValueError(
                f"El tamaño de la sala debe ser uno de {TAMAÑOS_VALIDOS}. "
                f"Se recibió: '{tamaño}'."
            )
        self.tamaño = tamaño

    def _establecer_precio_base(self, precio_base: float):
        if not isinstance(precio_base, (int, float)):
            raise TypeError("El precio base debe ser un número (int o float).")
        if precio_base <= 0:
            raise ValueError("El precio base debe ser mayor que cero.")
        self.precio_base = float(precio_base)


    def _construir_mapa_precios(self) -> np.ndarray:
        mapa = np.full((self.filas, self.sillas), self.precio_base, dtype=float)
        for zona, (inicio, fin) in self.zonas.items():
            if zona == ZONA_PREMIUM:
                mapa[inicio:fin + 1, :] = self.precio_base * FACTOR_PREMIUM
            elif zona == ZONA_INTERMEDIA:
                mapa[inicio:fin + 1, :] = self.precio_base * FACTOR_INTERMEDIA
            elif zona == ZONA_ULTIMA_FILA:
                mapa[inicio:fin + 1, :] = self.precio_base * FACTOR_ULTIMA_FILA
        return mapa


    def _zona_de_fila(self, indice_fila: int) -> int:
        for zona, (inicio, fin) in self.zonas.items():
            if inicio <= indice_fila <= fin:
                return zona
        raise ValueError(
            f"El índice de fila {indice_fila} está fuera del rango de la sala."
        )

    def _verificar_ocupacion_cargada(self):
        if self.mapa_ocupacion is None:
            raise ValueError(
                f"La sala '{self.nombre}' no tiene mapa de ocupación cargado. "
                "Cargue primero las entradas."
            )

    def _verificar_ingresos_construidos(self):
        if self.mapa_ingresos is None:
            raise ValueError(
                f"La sala '{self.nombre}' no tiene mapa de ingresos construido. "
                "Construya primero el mapa de ingresos."
            )


    def cargar_mapa_ocupacion(self, ruta_csv: str):
        try:
            archivo = open(ruta_csv, encoding="utf-8")
        except OSError:
            raise FileNotFoundError(
                f"No se encontró el archivo de entradas: '{ruta_csv}'."
            )

        mapa:            np.ndarray  = np.zeros((self.filas, self.sillas), dtype=int)
        entradas_validas: list[dict] = []

        with archivo:
            lector = csv.DictReader(archivo)
            for numero_fila, fila in enumerate(lector, start=2):
                try:
                    fila_asiento  = int(fila["fila"])
                    silla_asiento = int(fila["silla"])
                except (KeyError, ValueError):
                    print(
                        f"  [Advertencia] Fila {numero_fila} del CSV: "
                        "campos 'fila' o 'silla' inválidos. Se omite."
                    )
                    continue

                if not (1 <= fila_asiento <= self.filas):
                    print(
                        f"  [Advertencia] Fila {numero_fila}: fila de asiento "
                        f"{fila_asiento} fuera del rango [1, {self.filas}]. Se omite."
                    )
                    continue
                if not (1 <= silla_asiento <= self.sillas):
                    print(
                        f"  [Advertencia] Fila {numero_fila}: silla "
                        f"{silla_asiento} fuera del rango [1, {self.sillas}]. Se omite."
                    )
                    continue

                mapa[fila_asiento - 1, silla_asiento - 1] += 1
                entradas_validas.append({
                    "fecha":          fila.get("fecha", "").strip(),
                    "num_proyeccion": int(fila.get("num_proyeccion", 1)),
                    "hora":           int(fila.get("hora", 0)),
                    "fila":           fila_asiento,
                    "silla":          silla_asiento,
                    "edad":           int(fila.get("edad", 0)),
                    "sexo":           fila.get("sexo", "").strip().upper(),
                })

        self.mapa_ocupacion = mapa
        self._entradas      = entradas_validas


    def calcular_estadisticos_ocupacion(self) -> dict:
        self._verificar_ocupacion_cargada()

        promedio   = round(float(np.mean(self.mapa_ocupacion)), 2)
        desviacion = round(float(np.std(self.mapa_ocupacion)),  2)

        idx_max          = int(np.argmax(self.mapa_ocupacion))
        idx_min          = int(np.argmin(self.mapa_ocupacion))
        fila_max, col_max = np.unravel_index(idx_max, self.mapa_ocupacion.shape)
        fila_min, col_min = np.unravel_index(idx_min, self.mapa_ocupacion.shape)

        return {
            "promedio":   promedio,
            "desviacion": desviacion,
            "maximo":     int(self.mapa_ocupacion[fila_max, col_max]),
            "pos_max":    (int(fila_max) + 1, int(col_max) + 1),
            "minimo":     int(self.mapa_ocupacion[fila_min, col_min]),
            "pos_min":    (int(fila_min) + 1, int(col_min) + 1),
        }


    def construir_mapa_ingresos(self):
        self._verificar_ocupacion_cargada()
        self.mapa_ingresos = self.mapa_ocupacion * self.mapa_precios


    def analizar_por_zona(self) -> dict:
        self._verificar_ocupacion_cargada()
        self._verificar_ingresos_construidos()

        resultado: dict = {}
        for zona, (inicio, fin) in self.zonas.items():
            ocu_zona = self.mapa_ocupacion[inicio:fin + 1, :]
            ing_zona = self.mapa_ingresos[inicio:fin + 1, :]
            resultado[NOMBRE_ZONAS[zona]] = {
                "ocupacion_total":    int(np.sum(ocu_zona)),
                "ocupacion_promedio": round(float(np.mean(ocu_zona)), 2),
                "ingresos_totales":   float(np.sum(ing_zona)),
                "ingresos_promedio":  round(float(np.mean(ing_zona)), 2),
            }
        return resultado


    def construir_matriz_dia(self, fecha: str) -> tuple[np.ndarray, list[int]]:
        entradas_dia: list[dict] = [
            e for e in self._entradas if e["fecha"] == fecha
        ]
        if not entradas_dia:
            raise ValueError(
                f"No hay entradas para la fecha '{fecha}' "
                f"en la sala '{self.nombre}'."
            )

        proyecciones: list[int] = sorted(
            set(e["num_proyeccion"] for e in entradas_dia)
        )
        indice_proy: dict[int, int] = {p: i for i, p in enumerate(proyecciones)}

        matriz = np.zeros((len(proyecciones), self.filas, self.sillas), dtype=int)
        for entrada in entradas_dia:
            idx_p = indice_proy[entrada["num_proyeccion"]]
            fi    = entrada["fila"]  - 1
            si    = entrada["silla"] - 1
            if matriz[idx_p, fi, si] == 1:
                print(
                    f"  [Advertencia] Asiento fila {fi + 1}, silla {si + 1} "
                    f"duplicado en proyección {entrada['num_proyeccion']}. Se omite."
                )
                continue
            matriz[idx_p, fi, si] = 1

        return matriz, proyecciones

    def calcular_totales_dia(self,
                              matriz_dia:   np.ndarray,
                              proyecciones: list[int]) -> dict:
        total_por_proyeccion: np.ndarray = np.sum(matriz_dia, axis=(1, 2))
        total_por_silla:      np.ndarray = np.sum(matriz_dia, axis=0)

        total_por_zona: dict[str, int] = {}
        for zona, (inicio, fin) in self.zonas.items():
            total_por_zona[NOMBRE_ZONAS[zona]] = int(
                np.sum(total_por_silla[inicio:fin + 1, :])
            )

        return {
            "por_proyeccion": {
                proyecciones[i]: int(total_por_proyeccion[i])
                for i in range(len(proyecciones))
            },
            "por_silla": total_por_silla,
            "por_zona":  total_por_zona,
        }


    def construir_matriz_mensual(self) -> tuple[np.ndarray, list[str]]:
        if not self._entradas:
            raise ValueError(
                f"La sala '{self.nombre}' no tiene entradas cargadas."
            )

        fechas:       list[str]      = sorted(set(e["fecha"] for e in self._entradas))
        indice_fecha: dict[str, int] = {f: i for i, f in enumerate(fechas)}

        matriz = np.zeros((len(fechas), self.filas, self.sillas), dtype=int)
        for entrada in self._entradas:
            idx_d = indice_fecha[entrada["fecha"]]
            fi    = entrada["fila"]  - 1
            si    = entrada["silla"] - 1
            matriz[idx_d, fi, si] += 1

        return matriz, fechas

    def calcular_estadisticos_mensual(self,
                                       matriz_mensual: np.ndarray,
                                       fechas:         list[str]) -> dict:
        ocupacion_por_dia: np.ndarray = np.sum(matriz_mensual, axis=(1, 2))
        promedio_por_dia:  np.ndarray = np.round(
            np.mean(matriz_mensual, axis=(1, 2)), 2
        )
        idx_max = int(np.argmax(ocupacion_por_dia))
        idx_min = int(np.argmin(ocupacion_por_dia))

        return {
            "ocupacion_por_dia":   ocupacion_por_dia,
            "promedio_por_dia":    promedio_por_dia,
            "fecha_mayor_demanda": fechas[idx_max],
            "ocupacion_max":       int(ocupacion_por_dia[idx_max]),
            "fecha_menor_demanda": fechas[idx_min],
            "ocupacion_min":       int(ocupacion_por_dia[idx_min]),
        }


    def construir_matriz_demanda_sexo(self) -> tuple[np.ndarray, list[str]]:
        if not self._entradas:
            raise ValueError(
                f"La sala '{self.nombre}' no tiene entradas cargadas."
            )

        fechas:       list[str]      = sorted(set(e["fecha"] for e in self._entradas))
        indice_fecha: dict[str, int] = {f: i for i, f in enumerate(fechas)}

        matriz = np.zeros((len(fechas), TOTAL_ZONAS, TOTAL_SEXOS), dtype=int)
        for entrada in self._entradas:
            sexo = entrada["sexo"]
            if sexo not in SEXOS_VALIDOS:
                print(
                    f"  [Advertencia] Sexo '{sexo}' no válido. Se omite el registro."
                )
                continue
            idx_d    = indice_fecha[entrada["fecha"]]
            idx_zona = self._zona_de_fila(entrada["fila"] - 1)
            idx_sexo = SEXO_M if sexo == "M" else SEXO_F
            matriz[idx_d, idx_zona, idx_sexo] += 1

        return matriz, fechas