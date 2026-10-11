import tempfile
import unittest
from pathlib import Path

import database
import validaciones as v


class TestNumero(unittest.TestCase):
    def test_coma_decimal(self):
        self.assertEqual(v.a_numero("2,1", "X"), (2.1, None))

    def test_no_numerico(self):
        valor, error = v.a_numero("abc", "X")
        self.assertIsNone(valor)
        self.assertIn("número", error)

    def test_nan_e_infinito(self):
        for texto in ("nan", "inf"):
            valor, error = v.a_numero(texto, "X")
            self.assertIsNone(valor)
            self.assertIsNotNone(error)

    def test_entero_con_decimales(self):
        valor, error = v.a_numero("2.5", "X", entero=True)
        self.assertIsNone(valor)
        self.assertIn("entero", error)

    def test_opcional_vacio(self):
        self.assertEqual(v.a_numero("  ", "X", obligatorio=False), (None, None))

    def test_estricto_rechaza_cero(self):
        valor, error = v.a_numero("0", "X", estricto=True)
        self.assertIsNone(valor)
        self.assertIn("mayor que 0", error)


class TestValidarEmpresa(unittest.TestCase):
    def test_valida(self):
        datos, errores = v.validar_empresa("  Taller A ", "120", "4", "8")
        self.assertEqual(errores, [])
        self.assertEqual(datos, {"nombre": "Taller A", "area_m2": 120.0,
                                 "num_estaciones": 4, "num_operarios": 8})

    def test_sin_nombre(self):
        datos, errores = v.validar_empresa("", "120", "4", "8")
        self.assertIsNone(datos)
        self.assertEqual(len(errores), 1)

    def test_area_con_texto(self):
        datos, errores = v.validar_empresa("Taller A", "mucho", "4", "8")
        self.assertIsNone(datos)
        self.assertIn("Área", errores[0])

    def test_opcionales_vacios(self):
        datos, errores = v.validar_empresa("Taller A")
        self.assertEqual(errores, [])
        self.assertEqual(datos, {"nombre": "Taller A", "area_m2": None,
                                 "num_estaciones": None, "num_operarios": None})


class TestValidarEscenario(unittest.TestCase):
    def test_valido(self):
        datos, errores = v.validar_escenario("Condición base", "Base", "1", "40", "25", True, "60")
        self.assertEqual(errores, [])
        self.assertEqual(datos["num_recursos"], 1)
        self.assertIs(datos["obstaculos"], True)
        self.assertEqual(datos["tiempo_observacion_min"], 60.0)

    def test_tipo_invalido(self):
        datos, errores = v.validar_escenario("A", "Otro", "1")
        self.assertIsNone(datos)
        self.assertIn("Tipo", errores[0])

    def test_recursos_cero(self):
        datos, errores = v.validar_escenario("A", "Base", "0")
        self.assertIsNone(datos)
        self.assertEqual(len(errores), 1)

    def test_tiempo_observacion_cero(self):
        datos, errores = v.validar_escenario("A", "Base", "1", tiempo_observacion_min="0")
        self.assertIsNone(datos)
        self.assertEqual(len(errores), 1)


class TestValidarRegistro(unittest.TestCase):
    def test_valido(self):  # P04
        datos, errores = v.validar_registro("Almacén", "Corte", "18", "20", "2,1", "1,8", True)
        self.assertEqual(errores, [])
        self.assertEqual(datos["distancia_m"], 18.0)
        self.assertEqual(datos["tiempo_espera_min"], 2.1)
        self.assertIs(datos["atendida"], True)

    def test_distancia_negativa(self):  # P02
        datos, errores = v.validar_registro("Almacén", "Corte", "-5", "20", "2.1", "1.8", True)
        self.assertIsNone(datos)
        self.assertEqual(len(errores), 1)
        self.assertIn("negativo", errores[0])

    def test_varios_errores_juntos(self):
        datos, errores = v.validar_registro("", "Corte", "18", "abc", "2.1", "1.8", True)
        self.assertIsNone(datos)
        self.assertEqual(len(errores), 2)


class TestIntegracionConDatabase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self._tmp.name) / "test.db"
        database.inicializar()

    def tearDown(self):
        self._tmp.cleanup()

    def test_datos_validados_se_guardan(self):
        emp, _ = v.validar_empresa("Taller A", "120", "4", "8")
        empresa_id = database.crear_empresa(**emp)
        esc, _ = v.validar_escenario("Base A", "Base", "1", "40", "25", False, "60")
        escenario_id = database.crear_escenario(empresa_id, **esc)
        reg, _ = v.validar_registro("Almacén", "Corte", "18", "20", "2.1", "1.8", True)
        database.crear_registro(escenario_id, **reg)
        self.assertEqual(len(database.listar_registros(escenario_id)), 1)


if __name__ == "__main__":
    unittest.main()