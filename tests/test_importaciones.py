import tempfile
import unittest
from pathlib import Path

import database
import importacion

ENCABEZADO = "origen,destino,distancia_m,carga_kg,tiempo_espera_min,tiempo_recorrido_min,atendida"


class TestImportacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        database.DB_PATH = self.carpeta / "test.db"
        database.inicializar()

    def tearDown(self):
        self._tmp.cleanup()

    def archivo(self, contenido, codificacion="utf-8"):
        ruta = self.carpeta / "datos.csv"
        ruta.write_bytes(contenido.encode(codificacion))
        return ruta

    def test_csv_con_comas(self):
        ruta = self.archivo(
            f"{ENCABEZADO}\nAlmacén,Corte,10,5,2,3,Sí\nAlmacén,Corte,20,10,4,5,No\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(errores, [])
        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0]["distancia_m"], 10.0)
        self.assertIs(registros[0]["atendida"], True)
        self.assertIs(registros[1]["atendida"], False)

    def test_csv_punto_y_coma_con_coma_decimal(self):
        ruta = self.archivo(
            f"{ENCABEZADO.replace(',', ';')}\nAlmacén;Corte;18;20;2,1;1,8;si\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(errores, [])
        self.assertEqual(registros[0]["tiempo_espera_min"], 2.1)
        self.assertEqual(registros[0]["tiempo_recorrido_min"], 1.8)

    def test_faltan_columnas(self):  # P10
        ruta = self.archivo("origen,destino,distancia_m\nAlmacén,Corte,10\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(registros, [])
        self.assertEqual(len(errores), 1)
        self.assertIn("carga_kg", errores[0])

    def test_fila_invalida_bloquea_todo(self):
        ruta = self.archivo(
            f"{ENCABEZADO}\nAlmacén,Corte,10,5,2,3,Sí\nAlmacén,Corte,-5,5,2,3,Sí\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(registros, [])
        self.assertEqual(len(errores), 1)
        self.assertTrue(errores[0].startswith("Fila 3"))
        self.assertIn("negativo", errores[0])

    def test_fila_incompleta(self):
        ruta = self.archivo(f"{ENCABEZADO}\nAlmacén,Corte,10\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(registros, [])
        self.assertTrue(any("obligatorio" in e for e in errores))

    def test_solo_encabezado(self):
        registros, errores = importacion.leer_registros_csv(self.archivo(ENCABEZADO + "\n"))
        self.assertEqual(registros, [])
        self.assertIn("no contiene registros", errores[0])

    def test_archivo_inexistente(self):
        registros, errores = importacion.leer_registros_csv(self.carpeta / "no_existe.csv")
        self.assertEqual(registros, [])
        self.assertEqual(len(errores), 1)

    def test_codificacion_windows(self):
        ruta = self.archivo(f"{ENCABEZADO}\nAlmacén,Corte,10,5,2,3,Sí\n", codificacion="cp1252")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(errores, [])
        self.assertEqual(registros[0]["origen"], "Almacén")

    def test_ignora_filas_vacias_y_columnas_extra(self):
        ruta = self.archivo(
            f"{ENCABEZADO},nota\nAlmacén,Corte,10,5,2,3,Sí,medición 1\n,,,,,,,\n\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(errores, [])
        self.assertEqual(len(registros), 1)

    def test_leer_e_importar_a_la_base_de_datos(self):
        empresa_id = database.crear_empresa("Taller A")
        escenario_id = database.crear_escenario(empresa_id, "Base A", "Base")
        ruta = self.archivo(
            f"{ENCABEZADO}\nAlmacén,Corte,10,5,2,3,Sí\nAlmacén,Corte,15,4,1,2,No\n")
        registros, errores = importacion.leer_registros_csv(ruta)
        self.assertEqual(errores, [])
        self.assertEqual(database.crear_registros(escenario_id, registros), 2)
        guardados = database.listar_registros(escenario_id)
        self.assertEqual(len(guardados), 2)
        self.assertEqual(guardados[1]["atendida"], 0)


if __name__ == "__main__":
    unittest.main()