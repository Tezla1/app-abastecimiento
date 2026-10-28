"""Flujos de interfaz sin pantalla: vista ↔ controlador ↔ casos de uso."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PyQt6.QtWidgets import QApplication

from textilflow.container import construir
from textilflow.presentation import theme
from textilflow.presentation.app import AplicacionController
from textilflow.presentation.widgets.logo import logo_pixmap
from textilflow.version import VERSION

(DASH, TALLER, LAYOUT, MODELO, ROBOT, SIM, MAPA, REQ, CMP, RES, VAL, DATOS, GUIA) = range(13)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(theme.hoja_de_estilo())
    return app


@pytest.fixture
def ui(qapp, monkeypatch):
    c = construir(":memory:")
    ctl = AplicacionController(c)
    errores = []
    for v in ctl.ventana.findChildren(object):
        if hasattr(v, "error") and hasattr(v, "confirmar"):
            monkeypatch.setattr(v, "error", errores.append)
            monkeypatch.setattr(v, "confirmar", lambda m: True)
    ctl.iniciar()
    ctl.errores = errores
    ctl.c = c
    yield ctl
    c.db.close()


def con_demo(ui):
    ui.controladores[DATOS]._cargar_demo()
    assert ui.ctx.taller_id is not None


def test_version_y_logo_visibles(ui):
    from PyQt6.QtWidgets import QLabel
    assert VERSION in ui.ventana.windowTitle()
    assert not ui.ventana.windowIcon().isNull() and not logo_pixmap(48).isNull()
    assert any(VERSION in l.text() for l in ui.ventana.findChildren(QLabel))
    assert any(VERSION in l.text() for l in ui.controladores[GUIA].vista.findChildren(QLabel))


def test_sin_taller_pide_crear_uno(ui):
    ui.controladores[LAYOUT]._guardar_estacion({"id": None, "codigo": "A", "nombre": "", "funcion": "ALMACEN", "x": 0, "y": 0,
                                                "tiempo_proceso_min": 0, "capacidad": 1, "grupo": ""})
    assert "taller activo" in ui.errores[0]


def test_todas_las_paginas_se_abren_sin_taller_y_con_demo(ui):
    for ctl in ui.controladores:
        ctl.refrescar()
    con_demo(ui)
    for i in range(len(ui.controladores)):
        ui.ventana.ir_a(i)
    assert not ui.errores, ui.errores


def test_flujo_de_proceso_desde_formularios(ui):
    taller_c, layout_c, sim_c = ui.controladores[TALLER], ui.controladores[LAYOUT], ui.controladores[SIM]
    taller_c._guardar({"id": None, "nombre": "Mi taller", "area_m2": 100, "operadores": 5, "jornada_h": 8,
                       "origen_datos": "REAL", "observaciones": ""})
    assert ui.ctx.taller_id is not None and not ui.errores
    for cod, fun, x, t in (("A", "ALMACEN", 0, 0), ("P", "PROCESO", 10, 1.0), ("D", "DESPACHO", 20, 0)):
        layout_c._guardar_estacion({"id": None, "codigo": cod, "nombre": cod, "funcion": fun, "x": x, "y": 0,
                                    "tiempo_proceso_min": t, "capacidad": 1, "grupo": ""})
    layout_c.refrescar()
    for o, d in (("A", "P"), ("P", "D")):
        layout_c._guardar_conexion({"id": None, "origen": o, "destino": d, "distancia_m": 0, "ancho_m": 1.5, "bidireccional": True})
    layout_c._guardar_prenda({"id": None, "nombre": "Camisa", "peso_unidad_kg": 0.3, "unidades_por_lote": 10, "factor_proceso": 1})
    layout_c.refrescar()
    tid = ui.c.procesos.listar_tipos()[0].id
    layout_c._guardar_ruta({"id": None, "tipo_prenda_id": tid, "nombre": "Única", "fraccion_pct": 100, "secuencia": "A>P>D"})
    layout_c._guardar_pedido({"id": None, "tipo_prenda_id": tid, "cantidad": 30, "prioridad": 1, "llegada_min": 0,
                              "vencimiento_min": 0, "origen_datos": "REAL"})
    assert not ui.errores, ui.errores
    base = {"id": None, "nombre": "S0", "tipo": "MANUAL", "robot_id": None, "num_recursos": 1,
            "tiempo_observacion_min": 120, "velocidad_ms": 1.0, "capacidad_kg": 40, "t_carga_s": 0, "t_descarga_s": 0,
            "nodo_inicial": "A", "reposicionamiento": True, "politica": "PRIORIDAD", "balanceo": True,
            "factor_demanda_pct": 100, "variabilidad_pct": 0, "semilla": 1}
    sim_c.refrescar()
    sim_c._guardar(base)
    sim_c._guardar_y_simular()
    assert not ui.errores, ui.errores
    assert sim_c.vista.kpis[0]._valor.text() == "3/3"          # 3 lotes de 10 completados
    assert sim_c.vista.tabla.rowCount() == 1                    # solo Proceso es un área con tiempo


def test_mapa_anima_resalta_rutas_y_calor(ui):
    con_demo(ui)
    ui.ventana.ir_a(MAPA)
    m = ui.controladores[MAPA]
    v = m.vista
    v.combo_esc.setCurrentIndex(1)
    m._simular(v.combo_esc.currentData())
    mapa = v.mapa
    mapa.pausar()
    assert mapa.reproduciendo is False and len(mapa._recursos_items) == 2
    mapa.set_tiempo(150)
    assert v.estado_global.text().startswith("Lotes completados") and v.tabla_areas.rowCount() == 7
    p150 = mapa._arcos[frozenset(("A", "C"))].pen().widthF()
    mapa.set_tiempo(450)
    assert mapa._arcos[frozenset(("A", "C"))].pen().widthF() >= p150          # el calor se acumula con el tiempo
    mapa.set_modo_calor("ninguno")
    assert mapa._arcos[frozenset(("A", "C"))].pen().widthF() == 2
    m._nodo_clicado("B")
    assert v.tabla_rutas.rowCount() > 0 and len(mapa._resaltes) > 0
    ped = [v.combo_pedido.itemData(i) for i in range(v.combo_pedido.count()) if v.combo_pedido.itemData(i)][0]
    v.combo_pedido.setCurrentIndex(v.combo_pedido.findData(ped))
    ids = {v.tabla_rutas.item(i, 0).text().split()[0] for i in range(v.tabla_rutas.rowCount())}
    assert ids == {f"#{ped}"}
    v.slider.setValue(0)
    v.btn_reiniciar.click()
    assert mapa.tiempo == 0
    assert not ui.errores, ui.errores


def test_mapa_posicion_de_recursos_interpola(ui):
    from textilflow.presentation.viewmodels import AnimacionVM, NodoVM
    from textilflow.presentation.widgets.mapa_operativo import ESCALA
    mapa = ui.controladores[MAPA].vista.mapa
    mapa.dibujar([NodoVM("A", "A", "ALMACEN", 0, 0), NodoVM("B", "B", "PROCESO", 10, 0)], [])
    mapa.cargar_animacion(AnimacionVM(10.0, [(1, 2.0, 4.0, ("A", "B"), True, 5.0)], [], {}, 1, "A"))
    assert mapa._pos_recurso(1, 0.0)[0].x() == 0
    p, kg = mapa._pos_recurso(1, 3.0)
    assert p.x() == pytest.approx(5 * ESCALA) and kg == 5.0
    p, kg = mapa._pos_recurso(1, 9.0)
    assert p.x() == pytest.approx(10 * ESCALA) and kg == 0.0


def test_requerimientos_y_parametros(ui):
    con_demo(ui)
    ui.ventana.ir_a(REQ)
    c = ui.controladores[REQ]
    c._analizar(c.vista.combo.currentData(), 4)
    v = c.vista
    assert v.t_criticos.rowCount() >= 4 and v.t_barrido.rowCount() == 4 and v.t_norma.rowCount() >= 3
    assert v.k_reco._valor.text() == "2" and v.t_alertas.rowCount() > 0
    c._guardar_parametro("umbral_cuello_botella_pct", 95)
    assert next(p for p in c._lista if p.clave == "umbral_cuello_botella_pct").valor == 95
    c._restaurar()
    assert next(p for p in c._lista if p.clave == "umbral_cuello_botella_pct").valor == 85
    assert not ui.errores


def test_replicas_desde_la_interfaz(ui):
    con_demo(ui)
    ui.ventana.ir_a(SIM)
    c = ui.controladores[SIM]
    e = ui.c.escenarios.listar(ui.ctx.taller_id)[0]
    e.variabilidad_pct = 15
    ui.c.escenarios.guardar(e)
    c.refrescar()
    c._ejecutar_replicas(e.id, 8)
    assert c.vista.tabla_stats.rowCount() == 7 and c.vista.tabla_runs.rowCount() == 8
    assert c.vista.histo._bins


def test_alertas_en_insignia(ui):
    con_demo(ui)
    assert "Alertas:" in ui.ventana.insignia.text() and "críticas" in ui.ventana.insignia.text()
    ui.ventana.alertas_solicitadas.emit()
    assert ui.ventana.pagina_actual() == REQ


def test_comparacion_muestra_kpis_de_proceso(ui):
    con_demo(ui)
    ui.ventana.ir_a(CMP)
    ui.controladores[CMP].vista.barra.boton.click()
    v = ui.controladores[CMP].vista
    assert "comparables" in v.veredicto.text() and v.tabla.rowCount() == 6 and v.tabla_proceso.rowCount() == 7
    assert v.g_avance._series


def test_eliminar_taller_y_estado_vacio(ui):
    con_demo(ui)
    ui.controladores[TALLER]._eliminar(ui.ctx.taller_id)
    assert ui.ctx.taller_id is None
    for ctl in ui.controladores:
        ctl.refrescar()
    assert not ui.errores


def test_validacion_desde_data_manager(ui):
    con_demo(ui)
    ui.controladores[VAL]._ejecutar()
    assert ui.controladores[VAL].vista.k_fail._valor.text() == "0"


def test_rutas_en_vista_2d(ui):
    con_demo(ui)
    lc = ui.controladores[LAYOUT]
    lc._calcular_ruta("A", "E", 0.0)
    assert "A → C" in lc.vista.ruta_resumen.text() or "A → C" in lc.vista.ruta_tramos.item(0, 1).text()
    lc._calcular_ruta("A", "E", 5.0)
    assert "Sin ruta factible" in lc.vista.ruta_resumen.text()
