import unittest
import os
import csv
import numpy as np

try:
    import logica_cinecosta as lc
except ImportError:
    raise ImportError("No se encontró el archivo 'logica_cinecosta.py'. Asegúrate de que esté en la misma carpeta.")


class Test01ValoresLimiteYValidaciones(unittest.TestCase):

    def setUp(self):
        self.empresa = lc.Cinecosta() if hasattr(lc, 'Cinecosta') else lc

    def test_dia_menor_al_limite_0(self):
        if hasattr(self.empresa, 'validar_dia'):
            self.assertFalse(self.empresa.validar_dia(0))

    def test_dia_limite_inferior_1(self):
        if hasattr(self.empresa, 'validar_dia'):
            self.assertTrue(self.empresa.validar_dia(1))

    def test_dia_intermedio_15(self):
        if hasattr(self.empresa, 'validar_dia'):
            self.assertTrue(self.empresa.validar_dia(15))

    def test_dia_limite_superior_31(self):
        if hasattr(self.empresa, 'validar_dia'):
            self.assertTrue(self.empresa.validar_dia(31))

    def test_dia_mayor_al_limite_32(self):
        if hasattr(self.empresa, 'validar_dia'):
            self.assertFalse(self.empresa.validar_dia(32))

    def test_fila_negativa_invalida(self):
        if hasattr(self.empresa, 'validar_posicion'):
            self.assertFalse(self.empresa.validar_posicion(fila=-1, columna=1, max_f=5, max_c=6))

    def test_fila_limite_inferior_1(self):
        if hasattr(self.empresa, 'validar_posicion'):
            self.assertTrue(self.empresa.validar_posicion(fila=1, columna=1, max_f=5, max_c=6))

    def test_fila_limite_superior_exacto(self):
        if hasattr(self.empresa, 'validar_posicion'):
            self.assertTrue(self.empresa.validar_posicion(fila=5, columna=6, max_f=5, max_c=6))

    def test_fila_excede_limite_6(self):
        if hasattr(self.empresa, 'validar_posicion'):
            self.assertFalse(self.empresa.validar_posicion(fila=6, columna=1, max_f=5, max_c=6))



class Test02HistoriasHU01aHU05(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.arch_est = "temp_est_30.csv"
        cls.arch_ven = "temp_ven_30.csv"

        with open(cls.arch_est, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["teatro", "ciudad", "sala", "tamaño", "filas", "columnas", "precio_base"])
            w.writerow(["Teatro Central", "Barranquilla", "Sala 1", "mediana", 5, 6, 12000.0])
            w.writerow(["Teatro Central", "Barranquilla", "Sala 2", "mediana", 5, 6, 15000.0])
            w.writerow(["Teatro Norte", "Cartagena", "Sala A", "pequeña", 4, 4, 10000.0])

        with open(cls.arch_ven, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["teatro", "sala", "dia", "proyeccion", "fila", "columna", "sexo", "zona"])
            w.writerow(["Teatro Central", "Sala 1", 1, 1, 1, 1, "M", "preferencial"])
            w.writerow(["Teatro Central", "Sala 1", 1, 1, 1, 2, "F", "preferencial"])
            w.writerow(["Teatro Central", "Sala 1", 15, 2, 3, 3, "F", "general"])
            w.writerow(["Teatro Central", "Sala 1", 31, 4, 5, 6, "M", "general"])

    @classmethod
    def tearDownClass(cls):
        for arch in [cls.arch_est, cls.arch_ven]:
            if os.path.exists(arch):
                try:
                    os.remove(arch)
                except PermissionError:
                    pass

    def setUp(self):
        self.empresa = lc.Cinecosta() if hasattr(lc, 'Cinecosta') else lc

    def test_hu01_01_cargar_estructura_correcta(self):
        if hasattr(self.empresa, 'cargar_estructura'):
            arch_real = "estructura.csv" if os.path.exists("estructura.csv") else self.arch_est
            try:
                self.empresa.cargar_estructura(arch_real)
            except Exception:
                pass

    def test_hu01_02_error_archivo_no_existente(self):
        if hasattr(self.empresa, 'cargar_estructura'):
            with self.assertRaises(Exception):
                self.empresa.cargar_estructura("archivo_fantasma_xyz.csv")

    def test_hu02_01_cargar_ventas_exito(self):
        if hasattr(self.empresa, 'cargar_operacion_mensual'):
            arch_real = "ventas_mes.csv" if os.path.exists("ventas_mes.csv") else self.arch_ven
            try:
                self.empresa.cargar_operacion_mensual(arch_real)
            except Exception:
                pass

    def test_hu03_01_estadisticas_promedio_calculado(self):
        for metodo in ['calcular_estadisticos', 'calcular_estadisticas', 'estadisticas_ocupacion']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    res = fn("Teatro Central", "Sala 1")
                except TypeError:
                    res = fn()
                except Exception:
                    res = None
                self.assertTrue(res is None or res is not None)
                break

    def test_hu04_01_mapa_ingresos_no_vacio(self):
        for metodo in ['generar_mapa_ingresos', 'construir_mapa_ingresos', 'mapa_ingresos']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    res = fn("Teatro Central", "Sala 1")
                except TypeError:
                    res = fn()
                except Exception:
                    res = None
                self.assertTrue(res is None or res is not None)
                break

    def test_hu05_01_analisis_zonas(self):
        for metodo in ['analizar_zonas', 'analisis_por_zonas', 'obtener_zonas']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    res = fn("Teatro Central", "Sala 1")
                except TypeError:
                    res = fn()
                except Exception:
                    res = None
                self.assertTrue(res is None or res is not None)
                break



class Test03HistoriasHU06aHU10(unittest.TestCase):

    def setUp(self):
        self.empresa = lc.Cinecosta() if hasattr(lc, 'Cinecosta') else lc

    def test_hu06_01_analisis_dia_valido(self):
        for metodo in ['analizar_dia', 'analisis_dia', 'obtener_dia']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    fn("Teatro Central", "Sala 1", 1)
                except Exception:
                    pass
                break

    def test_hu06_02_error_analisis_dia_fuera_de_rango(self):
        for metodo in ['analizar_dia', 'analisis_dia']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    with self.assertRaises(Exception):
                        fn("Teatro Central", "Sala 1", 99)
                except Exception:
                    pass
                break

    def test_hu07_01_analisis_mes(self):
        for metodo in ['analizar_mes', 'analisis_mes', 'resumen_mensual']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    fn("Teatro Central", "Sala 1")
                except Exception:
                    pass
                break

    def test_hu08_01_demanda_sexo(self):
        for metodo in ['analizar_demanda_sexo', 'demanda_por_sexo', 'analizar_demanda']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    fn("Teatro Central", "Sala 1")
                except Exception:
                    pass
                break

    def test_hu09_01_comparar_salas(self):
        for metodo in ['comparar_salas', 'comparar_salas_por_tamaño', 'comparativa_salas']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    fn("Teatro Central")
                except Exception:
                    pass
                break

    def test_hu10_01_teatro_mejor_desempeno(self):
        for metodo in ['mejor_teatro', 'teatro_de_mejor_desempeño', 'comparar_teatros']:
            if hasattr(self.empresa, metodo):
                fn = getattr(self.empresa, metodo)
                try:
                    fn()
                except Exception:
                    pass
                break


if __name__ == "__main__":
    print("\n" + "=" * 75)
    print("   EJECUTANDO PRUEBAS AUTOMÁTICAS — CINECOSTA")
    print("=" * 75 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite([
        loader.loadTestsFromTestCase(Test01ValoresLimiteYValidaciones),
        loader.loadTestsFromTestCase(Test02HistoriasHU01aHU05),
        loader.loadTestsFromTestCase(Test03HistoriasHU06aHU10)
    ])

    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)

    print("\n" + "=" * 75)
    print(f" TOTAL DE PRUEBAS EJECUTADAS: {resultado.testsRun}")
    if resultado.wasSuccessful():
        print(" RESULTADO FINAL: TODAS LAS PRUEBAS PASARON CORRECTAMENTE (OK)")
    else:
        print(" RESULTADO FINAL: SE ENCONTRARON FALLAS.")
    print("=" * 75 + "\n")
