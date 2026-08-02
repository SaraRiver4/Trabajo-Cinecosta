import csv
import numpy as np

DIMENSIONES_TAMAÑO: dict[str, tuple[int, int]] ={
    "A": (8, 10),
    "B": (10, 12),
    "C": (12, 14)}

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
    "económica": 1,
    "premium": 2.5,
    "intermedia": 1.5,
    "última fila": 1.2
}

SEXOS: tuple[str, ...] = ("hombre", "mujer")

class Sala:
    def __init__(self,nombre: str,tamaño: str,precio_base: float,teatro: str = ""):

        tamaño = tamaño.upper()
        if tamaño not in DIMENSIONES_TAMAÑO:
            raise ValueError("El tamaño debe ser A, B o C")
        if precio_base <= 0:
            raise ValueError(
                "El precio base debe ser mayor que cero"
            )

        self.nombre: str = nombre
        self.tamaño: str = tamaño
        self.precio_base: float = precio_base
        self.teatro: str = teatro
        self.filas: int = DIMENSIONES_TAMAÑO[tamaño][0]
        self.sillas_por_fila: int = DIMENSIONES_TAMAÑO[tamaño][1]
        self.mapa_ocupación_mensual: np.ndarray | None = None
        self.mapa_ingresos_mensual: np.ndarray | None = None
        self.matriz_ocupación_día: np.ndarray | None = None
        self.matriz_demanda_sexo: np.ndarray | None = None

    def leer_csv(self,ruta_csv: str) -> list[dict[str, str]]:
        registros: list[dict[str, str]] = []
        try:
            archivo = open(ruta_csv,
                mode="r",
                encoding="utf-8",
                newline=""
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"No existe el archivo CSV: {ruta_csv}"
            )

        with archivo:
            lector = csv.DictReader(archivo)

            for fila in lector:
                if (
                    fila["teatro"].strip() == self.teatro
                    and fila["sala"].strip() == self.nombre
                ):
                    registros.append(fila)

        if len(registros) == 0:
            raise ValueError(
                f"No existen registros para la sala {self.nombre}")
        return registros

    def convertir_día(self, fecha: str) -> int:
        fecha = fecha.strip()

        if "-" in fecha:
            partes = fecha.split("-")
            return int(partes[2])

        if "/" in fecha:
            partes = fecha.split("/")
            return int(partes[0])

        raise ValueError(
            f"Formato de fecha no válido: {fecha}"
        )

    def validar_asiento(self,fila: int,silla: int) -> bool:
        return (
            1 <= fila <= self.filas
            and 1 <= silla <= self.sillas_por_fila
        )

    def zona_de_fila(self, fila: int) -> str:
        zonas = FILAS_ZONAS[self.tamaño]
        for zona, limites in zonas.items():
            fila_inicial, fila_final = limites
            if fila_inicial <= fila <= fila_final:
                return zona
            
        raise ValueError(
            f"La fila {fila} no pertenece a ninguna zona")

    def precio_de_silla(self, fila: int) -> float:
        zona = self.zona_de_fila(fila)
        factor = FACTORES_PRECIOS[zona]
        return self.precio_base * factor

    def construir_mapa_ocupación_mensual(self,ruta_csv: str) -> np.ndarray:
        registros = self.leer_csv(ruta_csv)
        días = [
            self.convertir_día(registro["fecha"])
            for registro in registros
        ]

        cantidad_días = max(días)
        mapa = np.zeros(
            (cantidad_días,self.filas,self.sillas_por_fila),dtype=int
        )

        for registro in registros:
            día = self.convertir_día(registro["fecha"])
            fila = int(registro["fila"])
            silla = int(registro["silla"])

            if not self.validar_asiento(fila, silla):
                continue
            mapa[día - 1, fila - 1, silla - 1] += 1

        self.mapa_ocupación_mensual = mapa
        return mapa

    def calcular_estadísticos_ocupación(self) -> dict:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación")

        mapa = self.mapa_ocupación_mensual

        promedio = float(np.mean(mapa))
        desviación = float(np.std(mapa))
        máximo = int(np.max(mapa))
        mínimo = int(np.min(mapa))

        posición_máxima = np.unravel_index(
            int(np.argmax(mapa)),
            mapa.shape
        )

        posición_mínima = np.unravel_index(
            int(np.argmin(mapa)),
            mapa.shape
        )

        return {
            "promedio": promedio,
            "desviación_estándar": desviación,
            "máximo": máximo,
            "mínimo": mínimo,
            "posición_máxima": posición_máxima,
            "posición_mínima": posición_mínima
        }

    def construir_mapa_ingresos_mensual(self) -> np.ndarray:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación"
            )

        precios = np.zeros(
            (
                self.filas,
                self.sillas_por_fila
            ),
            dtype=float
        )

        for fila in range(1, self.filas + 1):
            precio = self.precio_de_silla(fila)
            precios[fila - 1, :] = precio

        mapa_ingresos = (
            self.mapa_ocupación_mensual * precios
        )

        self.mapa_ingresos_mensual = mapa_ingresos

        return mapa_ingresos

    def analizar_zonas(self) -> dict:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación"
            )

        if self.mapa_ingresos_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ingresos"
            )

        resultados: dict = {}

        for zona, limites in FILAS_ZONAS[self.tamaño].items():
            fila_inicial, fila_final = limites

            ocupación_zona = (
                self.mapa_ocupación_mensual[
                    :,
                    fila_inicial - 1:fila_final,
                    :
                ]
            )

            ingresos_zona = (
                self.mapa_ingresos_mensual[
                    :,
                    fila_inicial - 1:fila_final,
                    :
                ]
            )

            cantidad_sillas = (
                fila_final - fila_inicial + 1
            ) * self.sillas_por_fila

            ocupación_total = int(
                np.sum(ocupación_zona)
            )

            ingresos_total = float(
                np.sum(ingresos_zona)
            )

            resultados[zona] = {
                "ocupación_total": ocupación_total,
                "ocupación_promedio": (
                    ocupación_total / cantidad_sillas
                ),
                "ingresos_total": ingresos_total,
                "ingresos_promedio": (
                    ingresos_total / cantidad_sillas
                )
            }

        return resultados

    def construir_matriz_ocupación_día(
        self,
        ruta_csv: str,
        día: int
    ) -> np.ndarray:
        registros = self.leer_csv(ruta_csv)

        registros_día: list[dict[str, str]] = []

        for registro in registros:
            día_registro = self.convertir_día(
                registro["fecha"]
            )

            if día_registro == día:
                registros_día.append(registro)

        if len(registros_día) == 0:
            raise ValueError(
                f"No existen registros para el día {día}"
            )

        identificadores = sorted(
            set(
                (
                    registro["fecha"],
                    registro["proyeccion"]
                )
                for registro in registros_día
            )
        )

        cantidad_proyecciones = len(identificadores)

        matriz = np.zeros(
            (
                self.filas,
                self.sillas_por_fila,
                cantidad_proyecciones
            ),
            dtype=int
        )

        posiciones = {
            identificador: índice
            for índice, identificador in enumerate(identificadores)
        }

        for registro in registros_día:
            fila = int(registro["fila"])
            silla = int(registro["silla"])

            if not self.validar_asiento(fila, silla):
                continue

            identificador = (
                registro["fecha"],
                registro["proyeccion"]
            )

            índice_proyección = posiciones[identificador]

            matriz[
                fila - 1,
                silla - 1,
                índice_proyección
            ] = 1

        self.matriz_ocupación_día = matriz

        return matriz

    def ocupación_por_proyección(self) -> np.ndarray:
        if self.matriz_ocupación_día is None:
            raise ValueError(
                "Primero debe construirse la matriz del día"
            )

        return np.sum(
            self.matriz_ocupación_día,
            axis=(0, 1)
        )

    def ocupación_por_silla_en_día(self) -> np.ndarray:
        if self.matriz_ocupación_día is None:
            raise ValueError(
                "Primero debe construirse la matriz del día"
            )

        return np.sum(
            self.matriz_ocupación_día,
            axis=2
        )

    def ocupación_por_zona_en_día(self) -> dict[str, int]:
        if self.matriz_ocupación_día is None:
            raise ValueError(
                "Primero debe construirse la matriz del día"
            )

        resultados: dict[str, int] = {}

        for zona, limites in FILAS_ZONAS[self.tamaño].items():
            fila_inicial, fila_final = limites

            valores = self.matriz_ocupación_día[
                fila_inicial - 1:fila_final,
                :,
                :
            ]

            resultados[zona] = int(np.sum(valores))

        return resultados

    def ocupación_total_por_día(self) -> np.ndarray:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación"
            )

        return np.sum(
            self.mapa_ocupación_mensual,
            axis=(1, 2)
        )

    def ocupación_promedio_por_día(self) -> np.ndarray:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación"
            )

        return np.mean(
            self.mapa_ocupación_mensual,
            axis=(1, 2)
        )

    def día_más_ocupado(self) -> int:
        totales = self.ocupación_total_por_día()

        return int(np.argmax(totales)) + 1

    def día_menos_ocupado(self) -> int:
        totales = self.ocupación_total_por_día()

        return int(np.argmin(totales)) + 1

    def construir_matriz_demanda_sexo(
        self,
        ruta_csv: str
    ) -> np.ndarray:
        registros = self.leer_csv(ruta_csv)

        días = [
            self.convertir_día(registro["fecha"])
            for registro in registros
        ]

        cantidad_días = max(días)

        matriz = np.zeros(
            (
                cantidad_días,
                4,
                2
            ),
            dtype=int
        )

        posiciones_sexo = {
            "hombre": 0,
            "mujer": 1
        }

        zonas = (
            "económica",
            "premium",
            "intermedia",
            "última fila"
        )

        posiciones_zona = {
            zona: índice
            for índice, zona in enumerate(zonas)
        }

        for registro in registros:
            día = self.convertir_día(registro["fecha"])
            fila = int(registro["fila"])
            sexo = registro["sexo"].strip().lower()

            if not self.validar_asiento(fila, 1):
                continue

            if sexo in ("m", "masculino", "hombre"):
                sexo = "hombre"
            elif sexo in ("f", "femenino", "mujer"):
                sexo = "mujer"
            else:
                continue

            zona = self.zona_de_fila(fila)

            matriz[
                día - 1,
                posiciones_zona[zona],
                posiciones_sexo[sexo]
            ] += 1

        self.matriz_demanda_sexo = matriz

        return matriz

    def demanda_por_día(self) -> np.ndarray:
        if self.matriz_demanda_sexo is None:
            raise ValueError(
                "Primero debe construirse la matriz por sexo" )

        return np.sum(
            self.matriz_demanda_sexo,
            axis=(1, 2)
        )

    def demanda_por_zona(self) -> np.ndarray:
        if self.matriz_demanda_sexo is None:
            raise ValueError(
                "Primero debe construirse la matriz por sexo"
            )

        return np.sum(
            self.matriz_demanda_sexo,
            axis=(0, 2)
        )

    def demanda_por_sexo(self) -> np.ndarray:
        if self.matriz_demanda_sexo is None:
            raise ValueError(
                "Primero debe construirse la matriz por sexo"
            )

        return np.sum(
            self.matriz_demanda_sexo,
            axis=(0, 1)
        )

    def ocupación_total(self) -> int:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación"
            )

        return int(np.sum(self.mapa_ocupación_mensual))

    def ingreso_total(self) -> float:
        if self.mapa_ingresos_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ingresos"
            )

        return float(np.sum(self.mapa_ingresos_mensual))

    def ocupación_promedio(self) -> float:
        if self.mapa_ocupación_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ocupación"
            )

        return float(np.mean(self.mapa_ocupación_mensual))

    def ingreso_promedio(self) -> float:
        if self.mapa_ingresos_mensual is None:
            raise ValueError(
                "Primero debe construirse el mapa de ingresos"
            )

        return float(np.mean(self.mapa_ingresos_mensual))
