import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PyQt6.QtWidgets import QApplication

from textilflow.container import construir
from textilflow.presentation import theme
from textilflow.presentation.app import AplicacionController
from textilflow.presentation.widgets.logo import logo_pixmap
from textilflow.version import VERSION

(DASH, TALLER, LAYOUT, MODELO, ROBOT, SIM, MAPA, REQ, CMP, RES, CONT, VAL, DATOS, GUIA) = range(14)


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
    # las páginas se construyen al visitarlas, así que se parchea la clase base y no cada vista
    from textilflow.presentation.widgets.common import PageView
    monkeypatch.setattr(PageView, "error", lambda self, m: errores.append(m))
    monkeypatch.setattr(PageView, "confirmar", lambda self, m: True)
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
    assert sim_c.vista.kpis[0]._valor.text() == "3/3"
    assert sim_c.vista.tabla.rowCount() == 1


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
    assert mapa._arcos[frozenset(("A", "C"))].pen().widthF() >= p150
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
    assert len(v.g_barrido._filas) == 4 and any(f[3] for f in v.g_barrido._filas)
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
    assert len(c.vista.estabilidad._filas) == 7


def test_alertas_en_insignia(ui):
    con_demo(ui)
    ui.ventana.show()
    ui.ventana.resize(1400, 800)  # ventana ancha: la cabecera muestra el texto completo
    QApplication.processEvents()
    ui.ventana.set_alertas(*ui.ventana._alertas_txt)
    assert "Alertas:" in ui.ventana.insignia.text() and "críticas" in ui.ventana.insignia.text()
    ui.ventana.alertas_solicitadas.emit()
    assert ui.ventana.pagina_actual() == REQ


def test_comparacion_muestra_kpis_de_proceso(ui):
    con_demo(ui)
    ui.ventana.ir_a(CMP)
    ui.controladores[CMP].vista.barra.boton.click()
    v = ui.controladores[CMP].vista
    assert "comparables" in v.veredicto.text() and v.tabla.rowCount() == 6 and v.tabla_proceso.rowCount() == 7
    assert v.g_avance._series and v.tarjetas._rejilla.count() == 6


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


def test_contingencias_cerrar_recalcula_y_genera_informe(ui):
    con_demo(ui)
    c = ui.controladores[CONT]
    ui.ventana.ir_a(CONT)
    p = c.vista.panel
    i = p.widget("codigo").findData("CO")
    p.widget("codigo").setCurrentIndex(i)
    p.widget("detalle").setPlainText("Falla del motor principal")
    p.btn_guardar.click()
    assert not ui.errores
    assert p.tabla.rowCount() == 1
    assert c.vista.tabla_rutas.rowCount() > 0 and c.vista.mapa._resaltes
    assert "CO" in ui.ctx.cerrados()
    nodos, _ = __import__("textilflow.presentation.controllers.base", fromlist=["x"]).construir_red(
        ui.c.layout, ui.ctx.taller_id, cerrados=ui.ctx.cerrados())
    assert [n.cerrado for n in nodos if n.codigo == "CO"] == [True]
    ui.ventana.ir_a(MAPA)
    ui.ventana.ir_a(DASH)


def test_contingencias_reabrir_y_eliminar(ui):
    con_demo(ui)
    c = ui.controladores[CONT]
    p = c.vista.panel
    p.widget("codigo").setCurrentIndex(p.widget("codigo").findData("CO"))
    p.btn_guardar.click()
    p.widget("vigente").setChecked(False)
    p.btn_guardar.click()
    assert ui.ctx.cerrados() == frozenset()
    p.btn_eliminar.click()
    assert p.tabla.rowCount() == 0


def test_cambio_de_tema_reconstruye_la_ventana(qapp):
    from textilflow.presentation.app import Aplicacion
    c = construir(":memory:")
    c.demo.execute()
    ap = Aplicacion(c, qapp)
    theme.aplicar("oscuro")
    ventana = ap.controlador.ventana
    ventana.resize(1400, 800)
    QApplication.processEvents()
    ap.alternar_tema()
    assert ap.controlador.ventana is ventana
    assert theme.tema_actual() == "claro" and theme.BG == "#F1F4FA"
    assert ap.controlador.ventana.btn_tema.text().strip() == "Tema oscuro"
    ap.alternar_tema()
    assert theme.tema_actual() == "oscuro"
    ap.controlador.ventana.antes_de_cerrar = None
    ap.controlador.ventana.close()
    theme.aplicar("oscuro")
    c.db.close()


def test_cambio_de_tema_conserva_taller_y_pagina_y_no_reconstruye_todo(qapp):
    from PyQt6.QtCore import QCoreApplication, QEvent
    from textilflow.presentation.app import Aplicacion
    c = construir(":memory:")
    c.demo.execute()
    ap = Aplicacion(c, qapp)
    try:
        ap.controlador.ventana.ir_a(SIM)
        taller = ap.controlador.ctx.taller_id
        base = len(ap.controlador.ventana.findChildren(object))
        for _ in range(3):
            ap.alternar_tema()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        ctl = ap.controlador
        assert theme.tema_actual() == "claro"
        assert ctl.ctx.taller_id == taller and ctl.ventana.pagina_actual() == SIM
        # solo la página visible está construida; las demás esperan a ser visitadas
        assert sum(ctl.controladores.construida(i) for i in range(14)) == 1
        assert len(ctl.ventana.findChildren(object)) <= base * 1.1
        for i in range(14):
            ctl.ventana.ir_a(i)
    finally:
        theme.aplicar("oscuro")
        ap.controlador.ventana.antes_de_cerrar = None
        ap.controlador.ventana.close()
        c.db.close()


def test_ventana_se_adapta_a_cualquier_tamano(ui):
    from PyQt6.QtWidgets import QScrollArea
    con_demo(ui)
    v = ui.ventana
    v.show()
    # el mínimo que exige la ventana cabe en una pantalla de 800x600
    assert v.minimumSizeHint().width() <= 800 and v.minimumSizeHint().height() <= 600
    for ancho, alto in [(1920, 1080), (1366, 700), (1024, 640), (800, 520), (640, 420)]:
        v.resize(ancho, alto)
        QApplication.processEvents()
        for i in range(len(ui.controladores)):
            v.ir_a(i)
        assert (v.width(), v.height()) == (ancho, alto)
    # cada página vive dentro de un área desplazable (no se recorta: aparecen barras)
    assert all(isinstance(v._pila.widget(i), QScrollArea) for i in range(len(ui.controladores)))
    # en ventanas angostas el menú queda en modo compacto y vuelve a lo normal al ensanchar
    v.resize(800, 520); QApplication.processEvents()
    assert v._compacto is True
    v.resize(1366, 760); QApplication.processEvents()
    assert v._compacto is False and v._grupo.button(0).text().strip() == "Dashboard"


def test_mapa_operativo_respeta_un_area_cerrada_despues_de_simular(ui):
    """Si se cierra un área después de animar, al volver al mapa se vuelve a simular y nada pasa por ella."""
    from textilflow.domain.entities import Cierre
    con_demo(ui)
    ui.ventana.ir_a(MAPA)
    m = ui.controladores[MAPA]
    esc = ui.c.escenarios.listar(ui.ctx.taller_id)[0]
    m._simular(esc.id)
    assert any("C" in mv.ruta for mv in m._resultado.proceso.movimientos)      # sin cierres, Corte sí se usa
    ui.c.cierres.guardar(Cierre(ui.ctx.taller_id, "C", "FALLA_MAQUINARIA", "", 0.0, 0.0, True, True))
    ui.ctx.cierres_cambiaron.emit()
    ui.ventana.ir_a(CONT)
    ui.ventana.ir_a(MAPA)
    assert not any("C" in mv.ruta for mv in m._resultado.proceso.movimientos)


def test_cerrar_con_cambios_pregunta_y_permite_cancelar_o_guardar(qapp, monkeypatch, tmp_path):
    from PyQt6.QtWidgets import QFileDialog, QMessageBox
    from textilflow.presentation.app import Aplicacion
    c = construir(":memory:")
    ap = Aplicacion(c, qapp)
    v = ap.controlador.ventana
    c.demo.execute()                                   # hay cambios sin guardar
    assert c.db.cambios_sin_guardar() > 0
    elegido = {}

    def falso_exec(self):
        elegido["texto"] = self.text()
        botones = {b.text(): b for b in self.buttons()}
        self._clic = botones[elegido["boton"]]

    monkeypatch.setattr(QMessageBox, "exec", falso_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clic)
    # 1) Cancelar: la ventana NO se cierra
    elegido["boton"] = "Cancelar"
    assert ap._antes_de_cerrar() is False and c.db.cambios_sin_guardar() > 0
    # 2) Guardar como…: crea el .rlr, marca guardado y deja cerrar
    destino = tmp_path / "mi_proyecto.rlr"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(destino), ""))
    elegido["boton"] = "Guardar como…"
    assert ap._antes_de_cerrar() is True and destino.exists() and c.db.cambios_sin_guardar() == 0
    # 3) sin cambios no pregunta
    elegido["boton"] = "Cancelar"
    assert ap._antes_de_cerrar() is True
    v.antes_de_cerrar = None
    v.close()
    c.db.close()


def test_respaldos_automaticos_conservan_los_ultimos_3_y_detectan_cierre_incorrecto(tmp_path):
    import time
    from textilflow.infrastructure.respaldos import Respaldos
    c = construir(":memory:")
    c.demo.execute()
    r = Respaldos(tmp_path / "resp", c.datos.exportar_proyecto, c.datos.restaurar_proyecto)
    for _ in range(5):
        r.crear()
        time.sleep(1.05)
    assert len(r.listar()) == 3 and all(f.suffix == ".rlr" for f, _ in r.listar())
    assert r.listar()[0][1] > r.listar()[-1][1]
    assert not r.sesion_anterior_incorrecta()
    r.marcar_abierta()
    assert r.sesion_anterior_incorrecta()
    r.marcar_cerrada()
    assert not r.sesion_anterior_incorrecta()
    n = len(c.talleres.listar())
    c.talleres.eliminar(c.talleres.listar()[0].id) if hasattr(c.talleres, "eliminar") else None
    r.restaurar(r.listar()[0][0])
    assert len(c.talleres.listar()) == n
    c.db.close()


def test_descripcion_clara_de_errores():
    import sqlite3
    from textilflow import registro
    for exc, palabra in [(sqlite3.OperationalError("database is locked"), "en uso"), (ZeroDivisionError(), "cero"),
                         (KeyError("x"), "interno"), (MemoryError(), "memoria")]:
        try:
            raise exc
        except Exception as e:
            d = registro.describir(type(e), e, e.__traceback__)
        assert palabra.lower() in (d["titulo"] + d["que"] + d["sugerencia"]).lower()
        assert "test_ui.py" in d["donde"] and d["resumen"].startswith(type(exc).__name__)


def test_error_no_controlado_muestra_cuadro_y_no_cierra(qapp, monkeypatch):
    import sys
    from textilflow.presentation import errores
    vistos = []
    monkeypatch.setattr(errores, "mostrar", lambda d, parent=None: vistos.append(d) or "seguir")
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    errores.instalar()
    try:
        1 / 0
    except ZeroDivisionError:
        sys.excepthook(*sys.exc_info())
    assert len(vistos) == 1 and "cero" in vistos[0]["que"] and vistos[0]["donde"]
    # el mismo error repetido enseguida no abre otro cuadro
    try:
        1 / 0
    except ZeroDivisionError:
        sys.excepthook(*sys.exc_info())
    assert len(vistos) == 1


def test_base_danada_ofrece_empezar_de_nuevo_y_conserva_copia(qapp, monkeypatch, tmp_path):
    from PyQt6.QtWidgets import QMessageBox
    from textilflow.presentation import arranque
    ruta = tmp_path / "datos.db"
    ruta.write_bytes(b"esto no es una base de datos sqlite" * 50)

    def falso_exec(self):
        self._clic = {b.text(): b for b in self.buttons()}["Empezar con una base nueva"]
    monkeypatch.setattr(QMessageBox, "exec", falso_exec)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: self._clic)
    c = arranque.abrir_contenedor(str(ruta))
    assert c is not None and len(c.talleres.listar()) == 1
    assert list(tmp_path.glob("*.danada.bak"))
    c.db.close()


def _esperar(qapp, condicion, ms=20000):
    import time
    t = time.monotonic()
    while not condicion() and time.monotonic() - t < ms / 1000:
        qapp.processEvents()
        time.sleep(0.005)
    return condicion()


def test_tarea_en_segundo_plano_con_progreso_y_cancelar(qapp, monkeypatch):
    """Con hilo real: la ventana sigue viva, hay avance y se puede cancelar; el resultado llega al terminar."""
    from textilflow.application.progreso import Cancelado
    from textilflow.presentation import tareas
    monkeypatch.setattr(tareas, "SINCRONO", False)
    monkeypatch.setattr(tareas, "RETRASO_DIALOGO_MS", 0)
    import time
    # termina bien
    salida = {}
    avances = []

    def trabajo(progreso):
        for i in range(5):
            progreso(i, 5, f"paso {i}")
            avances.append(i)
            time.sleep(0.02)
        return "hecho"
    tareas.ejecutar(None, "Prueba", trabajo, lambda r: salida.setdefault("r", r))
    assert tareas.hay_tarea_activa()
    assert _esperar(qapp, lambda: "r" in salida) and salida["r"] == "hecho" and avances == [0, 1, 2, 3, 4]
    assert not tareas.hay_tarea_activa()
    # se cancela
    estado = {}

    def largo(progreso):
        for i in range(1000):
            progreso(i, 1000, "")
            time.sleep(0.01)
        return "nunca"
    tareas.ejecutar(None, "Largo", largo, lambda r: estado.setdefault("fin", r), al_cancelar=lambda: estado.setdefault("cancelado", True))
    qapp.processEvents()
    tareas._activas[0].pedir_cancelar()
    assert _esperar(qapp, lambda: "cancelado" in estado) and "fin" not in estado
    # un ErrorDeNegocio llega a al_fallar sin cerrar nada
    from textilflow.application.errors import ErrorDeNegocio
    errs = []

    def malo(progreso):
        raise ErrorDeNegocio("el escenario no es simulable")
    tareas.ejecutar(None, "Malo", malo, lambda r: None, al_fallar=lambda e: errs.append(str(e)))
    assert _esperar(qapp, lambda: errs) and "simulable" in errs[0]


def test_replicas_reales_en_hilo_dan_el_mismo_resultado_que_en_linea(ui, monkeypatch):
    from textilflow.presentation import tareas
    con_demo(ui)
    ui.ventana.ir_a(SIM)
    esc = ui.c.escenarios.listar(ui.ctx.taller_id)[0]
    en_linea = ui.c.replicas.execute(esc.id, 6)
    monkeypatch.setattr(tareas, "SINCRONO", False)
    monkeypatch.setattr(tareas, "RETRASO_DIALOGO_MS", 0)
    c = ui.controladores[SIM]
    c._ejecutar_replicas(esc.id, 6)
    assert _esperar(QApplication.instance(), lambda: getattr(c, "_ultimas", None) is not None)
    assert [f["makespan_min"] for f in c._ultimas.filas] == [f["makespan_min"] for f in en_linea.filas]


def test_animacion_del_mapa_se_pausa_al_salir_de_la_pagina_y_se_reanuda(ui):
    con_demo(ui)
    ui.ventana.show()
    ui.ventana.ir_a(MAPA)
    m = ui.controladores[MAPA]
    m._simular(ui.c.escenarios.listar(ui.ctx.taller_id)[0].id)
    mapa = m.vista.mapa
    QApplication.processEvents()
    assert mapa.reproduciendo
    ui.ventana.ir_a(DASH)                  # se va a otra página: deja de consumir procesador
    QApplication.processEvents()
    assert not mapa.reproduciendo
    ui.ventana.ir_a(MAPA)                  # vuelve: continúa donde iba
    QApplication.processEvents()
    assert mapa.reproduciendo


def test_ninguna_pagina_desborda_horizontalmente_desde_800_px(ui):
    """Las filas se apilan en columna y las tarjetas se reparten en varias filas: sin desplazamiento lateral."""
    con_demo(ui)
    v = ui.ventana
    v.show()
    for ancho, alto in [(1366, 700), (1024, 640), (900, 600), (800, 520)]:
        v.resize(ancho, alto)
        QApplication.processEvents()
        disponible = ancho - (64 if ancho < 980 else 256) - 14
        for i in range(len(ui.controladores)):
            v.ir_a(i)
            QApplication.processEvents()
            minimo = v._pila.widget(i).widget().minimumSizeHint().width()
            assert minimo <= disponible, f"página {i} necesita {minimo}px y solo hay {disponible}px a {ancho}px de ventana"


def test_botones_estandar_de_qt_en_espanol(qapp):
    from PyQt6.QtWidgets import QMessageBox
    from textilflow.presentation import idioma
    assert idioma.instalar(qapp)
    c = QMessageBox()
    c.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
    c.setDetailedText("detalle")
    textos = {b.text().replace("&", "") for b in c.buttons()}
    assert {"Sí", "No", "Cancelar"} <= textos, textos
    assert any("detalles" in t.lower() for t in textos), textos
    assert not {"Yes", "Cancel", "Show Details..."} & textos


def test_validacion_muestra_estados_en_espanol(ui):
    con_demo(ui)
    ui.ventana.ir_a(VAL)
    ui.controladores[VAL]._ejecutar()
    v = ui.controladores[VAL].vista
    assert v.k_pass._titulo.text() == "APROBADO" and v.k_warn._titulo.text() == "ADVERTENCIA" and v.k_fail._titulo.text() == "FALLA"
    estados = {v.tabla.item(r, 0).text() for r in range(v.tabla.rowCount())}
    assert estados and estados <= {"APROBADO", "ADVERTENCIA", "FALLA"}


def test_todos_los_campos_tienen_ayuda_emergente():
    """Cada campo de formulario explica qué se debe escribir (unidad, rango, ejemplo)."""
    import re
    import glob
    import os
    carpeta = os.path.join(os.path.dirname(__file__), "..", "textilflow", "presentation", "views")
    total = 0
    for ruta in glob.glob(os.path.join(carpeta, "*.py")):
        fuente = open(ruta, encoding="utf-8").read()
        total += len(re.findall(r'CampoSpec\("', fuente))
        assert len(re.findall(r'ayuda="', fuente)) >= len(re.findall(r'CampoSpec\("', fuente)), ruta
    assert total >= 60
