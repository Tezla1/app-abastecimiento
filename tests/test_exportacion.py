import csv
import tempfile
import unittest
from pathlib import Path

import exportacion

FILAS = [
    {"clave": "tiempo_abastecimiento_prom", "indicador": "Tiempo promedio de abastecimiento (min)",
     "base": 9.0, "alternativo": 3.0, "variacion_pct": -66.6667},
    {"clave": "solicitudes_atendidas_pct", "indicador": "Solicitudes atendidas (%)",
     "base": 75.0, "alternativo": None, "variacion_pct": None},
]


class TestExportacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._tmp.name) / "salida.csv"

    def tearDown(self):
        self._tmp.cleanup()

    def leer(self):
        with open(self.ruta, newline="", encoding="utf-8-sig") as archivo:
            return list(csv.reader(archivo, delimiter=";"))

    def test_estructura_y_valores(self):
        exportacion.exportar_comparacion_csv(
            self.ruta, "Taller CSV", "Condición base", "Con recurso móvil", FILAS,
            fecha="2026-10-18 10:00")
        filas = self.leer()
        self.assertEqual(filas[0], list(exportacion.COLUMNAS))
        self.assertEqual(len(filas), 3)
        self.assertEqual(filas[1], [
            "Taller CSV", "Condición base", "Con recurso móvil",
            "Tiempo promedio de abastecimiento (min)", "9,00", "3,00", "-66,67",
            "2026-10-18 10:00"])

    def test_datos_faltantes_quedan_vacios(self):
        exportacion.exportar_comparacion_csv(
            self.ruta, "Taller CSV", "Condición base", "Con recurso móvil", FILAS)
        self.assertEqual(self.leer()[2][4:7], ["75,00", "", ""])

    def test_sin_alternativo(self):
        exportacion.exportar_comparacion_csv(
            self.ruta, "Taller CSV", "Condición base", None, FILAS)
        self.assertEqual(self.leer()[1][2], "")

    def test_incluye_bom_para_excel(self):
        exportacion.exportar_comparacion_csv(
            self.ruta, "Taller CSV", "Condición base", None, FILAS)
        self.assertTrue(self.ruta.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_nombre_archivo_seguro(self):
        self.assertEqual(
            exportacion.nombre_archivo_seguro("Taller CSV: base/alt?"), "Taller_CSV_base_alt")
        self.assertEqual(exportacion.nombre_archivo_seguro("???"), "resultados")


if __name__ == "__main__":
    unittest.main()