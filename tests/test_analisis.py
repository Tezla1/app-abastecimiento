import tempfile
import unittest
from pathlib import Path

import analisis
import database


def _registro(dist, carga, espera, recorrido, atendida):
    return dict(origen="Almacén", destino="Corte", distancia_m=dist, carga_kg=carga,
                tiempo_espera_min=espera, tiempo_recorrido_min=recorrido, atendida=atendida)


BASE = [_registro(10, 5, 2, 3, True), _registro(20, 10, 4, 5, True),
        _registro(30, 8, 6, 7, True), _registro(15, 4, 1, 2, False)]
MOVIL = [_registro(10, 5, 1, 2, True) for _ in range(4)]


class TestAnalisis(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self._tmp.name) / "test.db"
        database.inicializar()
        self.empresa = database.crear_empresa("Taller A")
        self.base = self._escenario("Condición base", "Base", BASE)
        self.movil = self._escenario("Con recurso móvil", "Recurso móvil", MOVIL)
        self.vacio = self._escenario("Sin registros", "Base", [])

    def tearDown(self):
        self._tmp.cleanup()

    def _escenario(self, nombre, tipo, registros, t_obs=60):
        escenario_id = database.crear_escenario(
            self.empresa, nombre, tipo, tiempo_observacion_min=t_obs)
        if registros:
            database.crear_registros(escenario_id, registros)
        return next(e for e in database.listar_escenarios(self.empresa)
                    if e["id"] == escenario_id)

    def test_comparacion_completa(self):
        r = analisis.comparar_escenarios(self.base, self.movil)
        self.assertTrue(r["comparable"])
        self.assertEqual(r["avisos"], [])
        filas = {f["clave"]: f for f in r["filas"]}
        self.assertAlmostEqual(filas["tiempo_abastecimiento_prom"]["base"], 9.0)
        self.assertAlmostEqual(filas["tiempo_abastecimiento_prom"]["alternativo"], 3.0)
        self.assertAlmostEqual(filas["tiempo_abastecimiento_prom"]["variacion_pct"], -200 / 3)
        self.assertAlmostEqual(filas["solicitudes_atendidas_pct"]["variacion_pct"], 100 / 3)
        self.assertAlmostEqual(filas["utilizacion_pct"]["alternativo"], 8 / 60 * 100)

    def test_sin_alternativo(self):
        r = analisis.comparar_escenarios(self.base)
        self.assertIsNone(r["ind_alt"])
        self.assertFalse(r["comparable"])
        self.assertTrue(all(f["variacion_pct"] is None for f in r["filas"]))

    def test_mismo_escenario_no_se_compara_consigo_mismo(self):
        r = analisis.comparar_escenarios(self.base, self.base)
        self.assertIsNone(r["ind_alt"])
        self.assertFalse(r["comparable"])
        self.assertEqual(len(r["avisos"]), 1)
        self.assertIn("mismo escenario", r["avisos"][0])

    def test_alternativo_vacio_no_es_comparable(self):
        r = analisis.comparar_escenarios(self.base, self.vacio)
        self.assertFalse(r["comparable"])
        self.assertTrue(r["avisos"])
        self.assertTrue(all(f["variacion_pct"] is None for f in r["filas"]))

    def test_aviso_si_la_utilizacion_supera_100(self):
        corto = self._escenario("Observación corta", "Base", BASE, t_obs=5)
        r = analisis.comparar_escenarios(corto)
        self.assertTrue(any("100 %" in a for a in r["avisos"]))


if __name__ == "__main__":
    unittest.main()