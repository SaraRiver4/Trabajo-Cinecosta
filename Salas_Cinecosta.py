import csv 
import numpy as np 


class Salas:

    def __init__(self, nombre_teatro: str,
                ciudad: str, nombre_sala: str,
                tamanio_sala: str, precio_base: float):
        
        self.nombre_teatro = nombre_teatro
        self.ciudad = ciudad
        self.nombre_sala = nombre_sala
        self.tamanio_sala = tamanio_sala
        self.precio_base = float(precio_base)
 
    def establecer_dimensiones(self, tamanio: str):
        if not isinstance(tamanio, str):
            raise TypeError("El tamaño de la sala debe ser tipo str.")
        self.tamanio_sala = tamanio.upper()
        if self.tamanio_sala == 'A':
            self.filas, self.columnas = 8, 10
        elif self.tamanio_sala == 'B':
            self.filas, self.columnas = 10, 12
        elif self.tamanio_sala == 'C':
            self.filas, self.columnas = 12, 14
        else:
            raise ValueError("El tamaño de la sala debe ser A, B o C.")

    def obtener_limites_zonas(self) -> list:
        if self.tamanio_sala == "A":
            return [(0, 3), (3, 5), (5, 7), (7, 8)]
        if self.tamanio_sala == "B":
            return [(0, 4), (4, 6), (6, 9), (9, 10)]
        if self.tamanio_sala == "C":
            return [(0, 5), (5, 7), (7, 11), (11, 12)]
        return []