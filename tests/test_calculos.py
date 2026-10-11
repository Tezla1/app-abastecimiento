import unittest

import calculos

ESC = {"num_recursos": 1, "tiempo_observacion_min": 60}


def reg(dist, carga, espera, recorrido, atendida):
    return {
        "distancia_m": dist, "carga_kg": carga,
        "tiempo_espera_min": espera, "tiempo_recorrido_min": recorrido,
        "atendida": atendida,
    }


REGISTROS_BASE = [
    reg(10, 5, 2, 3, 1),
    reg(20, 10, 4, 5, 1),
    reg(30, 8, 6, 7, 1),
    reg(15, 4, 1, 2, 0),  # no atendida: no entra en promedios ni en distancia
]

REGISTROS_ALT = [reg(10, 5, 1, 2, 1) for _ in range(4)]


class TestIndicadores(unittest.TestCase):
    def test_escenario_base(self):
        ind = calculos.calcular_indicadores(ESC, REGISTROS_BASE)
        self.assertAlmostEqual(ind["solicitudes_atendidas_pct"], 75.0)
        self.assertAlmostEqual(ind["distancia_total"], 60.0)
        self.assertAlmostEqual(ind["distancia_prom"], 20.0)
        self.assertAlmostEqual(ind["tiempo_abastecimiento_prom"], 9.0)
        self.assertAlmostEqual(ind["espera_prom"], 4.0)
        self.assertAlmostEqual(ind["utilizacion_pct"], 25.0)

    def test_escenario_alternativo(self):
        ind = calculos.calcular_indicadores(ESC, REGISTROS_ALT)
        self.assertAlmostEqual(ind["solicitudes_atendidas_pct"], 100.0)
        self.assertAlmostEqual(ind["distancia_total"], 40.0)
        self.assertAlmostEqual(ind["tiempo_abastecimiento_prom"], 3.0)
        self.assertAlmostEqual(ind["espera_prom"], 1.0)
        self.assertAlmostEqual(ind["utilizacion_pct"], 8 / 60 * 100)

    def test_sin_registros(self):
        ind = calculos.calcular_indicadores(ESC, [])
        self.assertEqual(ind["n_registros"], 0)
        self.assertIsNone(ind["tiempo_abastecimiento_prom"])
        self.assertIsNone(ind["solicitudes_atendidas_pct"])

    def test_ninguna_atendida(self):
        ind = calculos.calcular_indicadores(ESC, [reg(10, 5, 1, 2, 0)])
        self.assertEqual(ind["solicitudes_atendidas_pct"], 0)
        self.assertIsNone(ind["tiempo_abastecimiento_prom"])
        self.assertIsNone(ind["distancia_total"])

    def test_utilizacion_sin_tiempo_observacion(self):
        esc = {"num_recursos": 1, "tiempo_observacion_min": None}
        ind = calculos.calcular_indicadores(esc, REGISTROS_BASE)
        self.assertIsNone(ind["utilizacion_pct"])
        self.assertIsNotNone(ind["distancia_total"])

    def test_utilizacion_con_varios_recursos(self):
        esc = {"num_recursos": 2, "tiempo_observacion_min": 60}
        ind = calculos.calcular_indicadores(esc, REGISTROS_BASE)
        self.assertAlmostEqual(ind["utilizacion_pct"], 12.5)


class TestComparacion(unittest.TestCase):
    def setUp(self):
        self.base = calculos.calcular_indicadores(ESC, REGISTROS_BASE)
        self.alt = calculos.calcular_indicadores(ESC, REGISTROS_ALT)

    def test_variacion_basica(self):
        self.assertAlmostEqual(calculos.variacion_pct(9, 3), -66.6666667)

    def test_variacion_base_cero(self):
        self.assertIsNone(calculos.variacion_pct(0, 5))

    def test_variacion_con_dato_faltante(self):
        self.assertIsNone(calculos.variacion_pct(None, 5))

    def test_comparar_valores(self):
        filas = {f["clave"]: f for f in calculos.comparar(self.base, self.alt)}
        self.assertAlmostEqual(filas["tiempo_abastecimiento_prom"]["variacion_pct"], -66.6666667)
        self.assertAlmostEqual(filas["distancia_total"]["variacion_pct"], -33.3333333)
        self.assertAlmostEqual(filas["espera_prom"]["variacion_pct"], -75.0)
        self.assertAlmostEqual(filas["solicitudes_atendidas_pct"]["variacion_pct"], 33.3333333)

    def test_escenarios_comparables(self):
        ok, problemas = calculos.verificar_comparable(self.base, self.alt)
        self.assertTrue(ok)
        self.assertEqual(problemas, [])

    def test_escenario_vacio_no_es_comparable(self):
        vacio = calculos.calcular_indicadores(ESC, [])
        ok, problemas = calculos.verificar_comparable(self.base, vacio)
        self.assertFalse(ok)
        self.assertEqual(len(problemas), 1)


if __name__ == "__main__":
    unittest.main()