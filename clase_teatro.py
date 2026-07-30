import numpy as np
from sala import Sala


class Teatro:

    def __init__(self, nombre: str, ciudad: str):
        self.establecer_nombre(nombre)
        self.establecer_ciudad(ciudad)
        self.salas: list[Sala] = []

    def establecer_nombre(self, nombre: str):
        if not isinstance(nombre, str):
            raise TypeError("El nombre del teatro debe ser una cadena de texto.")
        texto_limpio = nombre.strip()
        if texto_limpio == "":
            raise ValueError("El nombre del teatro no puede estar vacío.")
        self.nombre = texto_limpio

    def establecer_ciudad(self, ciudad: str):
        if not isinstance(ciudad, str):
            raise TypeError("La ciudad del teatro debe ser una cadena de texto.")
        texto_limpio = ciudad.strip()
        if texto_limpio == "":
            raise ValueError("La ciudad del teatro no puede estar vacía.")
        self.ciudad = texto_limpio

    def agregar_sala(self, sala: Sala):
        if not isinstance(sala, Sala):
            raise TypeError("El objeto sala debe ser una instancia de la clase Sala.")
        if sala.nombre in self.salas:
            raise ValueError(f"La sala '{sala.nombre}' ya existe en el teatro '{self.nombre}'.")
        self.salas.append(sala)

    def obtener_sala(self, nombre_sala: str) -> Sala:
        if nombre_sala not in self.salas:
            raise ValueError(f"La sala '{nombre_sala}' no existe en el teatro '{self.nombre}'.")
        for sala in self.salas:
            if sala.nombre.lower() == nombre_sala.lower():
                return sala
        return None

    

    def comparar_mapas_ingresos_por_tamaño(self) -> dict:
        grupos: dict[str, list[Sala]] = {}
        for sala in self.salas:
            if sala.mapa_ingresos is not None:
                if sala.tamaño not in grupos:
                    grupos[sala.tamaño] = []
                grupos[sala.tamaño].append(sala)

        grupos_validos = {t: ss for t, ss in grupos.items() if len(ss) >= 2}
        if not grupos_validos:
            raise ValueError(
                f"El teatro '{self.nombre}' no tiene al menos dos salas "
                "del mismo tamaño con mapas de ingresos construidos."
            )

        resultado: dict = {}
        for tamaño, salas_grupo in grupos_validos.items():
            cubo             = np.stack([s.mapa_ingresos for s in salas_grupo])
            ingresos_totales = np.sum(cubo, axis=(1, 2))
            idx_max          = int(np.argmax(ingresos_totales))
            mapa_promedio    = np.mean(cubo, axis=0)
            diferencias      = [cubo[i] - mapa_promedio for i in range(len(salas_grupo))]

            resultado[tamaño] = {
                "salas":              [s.nombre for s in salas_grupo],
                "ingresos_totales":   [float(v) for v in ingresos_totales],
                "sala_mayor_ingreso": salas_grupo[idx_max].nombre,
                "mapa_promedio":      mapa_promedio,
                "diferencias":        diferencias,
            }
        return resultado

    def comparar_mapas_ingresos_por_tamaño(self) -> dict:
        grupos: dict[str, list[Sala]] = {}
        for sala in self.salas:
            if sala.mapa_ingresos is not None:
                if sala.tamaño not in grupos:
                    grupos[sala.tamaño] = []
                grupos[sala.tamaño].append(sala)

        if len(grupos) < 2:
            raise ValueError(
                f"El teatro '{self.nombre}' no tiene al menos dos salas del mismo tamaño con mapas de ingresos construidos.")
        ingresos_por_tamaño: dict[str, list[float]] = {}
        for tamaño, salas_grupo in grupos.items():
            ingresos_totales = [float(np.sum(sala.mapa_ingresos)) for sala in salas_grupo]
            ingresos_por_tamaño[tamaño] = ingresos_totales
        idx_mejor_ingreso = int(np.argmax(ingresos_totales))
        mapas: dict[str] = {}
        for tamaño, salas_grupo in grupos.items():
            mapas.append(sala.mapa_ingresos)
        matrices_apiladas = np.stack(mapas)
        mapa_promedio = np.round(np.mean(matrices_apiladas, axis=0),2)
        return grupos, idx_mejor_ingreso, mapa_promedio
