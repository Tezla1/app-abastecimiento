# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Pruebas de las fórmulas de calculos.py con casos hechos a mano: indicadores, variación y comparabilidad.

import pytest

from textilflow.domain import calculos


def reg(atendida, espera, recorrido, dist):
    return {"atendida": atendida, "tiempo_espera_min": espera,
            "tiempo_recorrido_min": recorrido, "distancia_m": dist}


ESC = {"num_recursos": 2, "tiempo_observacion_min": 60}
REGS = [reg(1, 1.0, 3.0, 30), reg(1, 3.0, 5.0, 50), reg(0, 0, 0, 0)]


def test_indicadores_a_mano():
    ind = calculos.calcular_indicadores(ESC, REGS)
    assert ind["solicitudes_atendidas_pct"] == pytest.approx(200 / 3)
    assert ind["tiempo_abastecimiento_prom"] == pytest.approx(6.0)
    assert ind["distancia_total"] == 80
    assert ind["distancia_prom"] == 40
    assert ind["espera_prom"] == pytest.approx(2.0)
    assert ind["utilizacion_pct"] == pytest.approx(8 / 120 * 100)


def test_sin_registros_o_sin_atendidas():
    assert calculos.calcular_indicadores(ESC, [])["tiempo_abastecimiento_prom"] is None
    ind = calculos.calcular_indicadores(ESC, [reg(0, 0, 0, 0)])
    assert ind["solicitudes_atendidas_pct"] == 0 and ind["distancia_total"] is None


def test_variacion_y_comparable():
    assert calculos.variacion_pct(100, 80) == -20
    assert calculos.variacion_pct(0, 5) is None and calculos.variacion_pct(None, 5) is None
    ok = calculos.calcular_indicadores(ESC, REGS)
    vacio = calculos.calcular_indicadores(ESC, [])
    assert calculos.verificar_comparable(ok, ok) == (True, [])
    comparable, problemas = calculos.verificar_comparable(ok, vacio)
    assert not comparable and "alternativo" in problemas[0]
