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


    def test_contar_registros_de_la_empresa(self):
        e = database.crear_empresa("Taller A")
        s1 = database.crear_escenario(e, "Base A", "Base")
        s2 = database.crear_escenario(e, "Móvil A", "Recurso móvil")
        database.crear_registro(s1, "Almacén", "Corte", 10, 5, 2, 3, True)
        database.crear_registro(s2, "Almacén", "Corte", 10, 5, 1, 2, True)
        self.assertEqual(database.contar_registros_empresa(e), 2)

    def test_crear_registros_varios(self):
        e = database.crear_empresa("Taller A")
        s = database.crear_escenario(e, "Base A", "Base")
        lote = [
            dict(origen="Almacén", destino="Corte", distancia_m=10, carga_kg=5,
                 tiempo_espera_min=2, tiempo_recorrido_min=3, atendida=True),
            dict(origen="Almacén", destino="Corte", distancia_m=15, carga_kg=4,
                 tiempo_espera_min=1, tiempo_recorrido_min=2, atendida=False),
        ]
        self.assertEqual(database.crear_registros(s, lote), 2)
        self.assertEqual(len(database.listar_registros(s)), 2)

    def test_crear_registros_es_atomico(self):
        e = database.crear_empresa("Taller A")
        s = database.crear_escenario(e, "Base A", "Base")
        lote = [
            dict(origen="A", destino="B", distancia_m=10, carga_kg=5,
                 tiempo_espera_min=1, tiempo_recorrido_min=2, atendida=True),
            dict(origen="A", destino="B", distancia_m=-5, carga_kg=5,
                 tiempo_espera_min=1, tiempo_recorrido_min=2, atendida=True),
        ]
        with self.assertRaises(sqlite3.IntegrityError):
            database.crear_registros(s, lote)
        self.assertEqual(database.listar_registros(s), [])


if __name__ == "__main__":
    unittest.main()