import sqlite3
import tempfile
import unittest
from pathlib import Path

import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self._tmp.name) / "test.db"
        database.inicializar()

    def tearDown(self):
        self._tmp.cleanup()

    def test_crear_y_listar_empresa(self):
        database.crear_empresa("Taller A", 120, 4, 8)
        empresas = database.listar_empresas()
        self.assertEqual(len(empresas), 1)
        self.assertEqual(empresas[0]["nombre"], "Taller A")

    def test_cascada_al_eliminar_empresa(self):
        e = database.crear_empresa("Taller A")
        s = database.crear_escenario(e, "Condición base", "Base", tiempo_observacion_min=60)
        database.crear_registro(s, "Almacén", "Corte", 18, 20, 2.1, 1.8, True)
        database.eliminar_empresa(e)
        self.assertEqual(database.listar_escenarios(e), [])
        self.assertEqual(database.listar_registros(s), [])

    def test_rechaza_distancia_negativa(self):
        e = database.crear_empresa("Taller A")
        s = database.crear_escenario(e, "Condición base", "Base")
        with self.assertRaises(sqlite3.IntegrityError):
            database.crear_registro(s, "Almacén", "Corte", -5, 20, 2.1, 1.8, True)

    def test_escenario_requiere_empresa_existente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            database.crear_escenario(999, "X", "Base")


if __name__ == "__main__":
    unittest.main()