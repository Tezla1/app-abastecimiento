import math

import pytest

from textilflow.domain import analisis, estadistica, normativa
from textilflow.domain.alertas import validar_rutas
from textilflow.domain.entities import (Conexion, Estacion, Parametro, Pedido, Robot, RutaProceso, TipoPrenda)
from textilflow.domain.routing import arcos_criticos, nodos_criticos, red_conexa, ruta_mas_corta
from textilflow.domain.simulacion import ParametrosSimulacion, generar_lotes, simular


def con(o, d, dist, ancho=1.5, bi=True):
    return Conexion(1, o, d, dist, ancho, bi)


def test_ruta_mas_corta_y_filtro_de_ancho():
    red = [con("A", "B", 5, 2.0), con("B", "C", 5, 2.0), con("A", "C", 8, 0.5)]
    assert ruta_mas_corta(red, "A", "C").nodos == ("A", "C")
    r = ruta_mas_corta(red, "A", "C", ancho_min_m=1.0)
    assert r.nodos == ("A", "B", "C") and r.distancia_m == 10 and r.ancho_min_m == 2.0
    assert ruta_mas_corta(red, "A", "C", ancho_min_m=3.0) is None


def test_sentido_unico_y_conexidad():
    assert ruta_mas_corta([con("A", "B", 5, bi=False)], "B", "A") is None
    assert red_conexa(["A", "B", "C"], [con("A", "B", 1), con("B", "C", 1)])
    assert not red_conexa(["A", "B", "C"], [con("A", "B", 1)])


def test_nodos_y_arcos_criticos():
    red = [con("A", "B", 1), con("B", "C", 1), con("B", "D", 1), con("C", "D", 1)]
    assert nodos_criticos(["A", "B", "C", "D"], red) == {"B": 2}
    assert [(c.origen, c.destino) for c in arcos_criticos(["A", "B", "C", "D"], red)] == [("A", "B")]
    anillo = [con("A", "B", 1), con("B", "C", 1), con("C", "A", 1)]
    assert not nodos_criticos(["A", "B", "C"], anillo) and not arcos_criticos(["A", "B", "C"], anillo)


def red_lineal(t_proc=1.0, puestos=1):
    est = [Estacion(1, "A", "Almacén", "ALMACEN", 0, 0, 0, 1), Estacion(1, "P", "Proceso", "PROCESO", 10, 0, t_proc, puestos),
           Estacion(1, "D", "Despacho", "DESPACHO", 20, 0, 0, 1)]
    return est, [con("A", "P", 10), con("P", "D", 10)]


def prm(**kw):
    base = dict(num_recursos=1, velocidad_ms=1.0, capacidad_kg=100, t_carga_s=0, t_descarga_s=0, nodo_inicial="A",
                reposicionamiento=True, ancho_requerido_m=0.0, tiempo_observacion_min=120)
    base.update(kw)
    return ParametrosSimulacion(**base)


def correr(pedidos, est, cons, p=None, secuencia="A>P>D", lote=10, peso=1.0):
    tipo = TipoPrenda("Camisa", peso, lote, 1.0, id=1)
    ruta = RutaProceso(1, 1, "Única", 100, secuencia, id=1)
    return simular(p or prm(), est, cons, [tipo], [ruta], pedidos)


def test_un_lote_tiempo_exacto():
    est, cons = red_lineal()
    r = correr([Pedido(1, 1, 10, 3, 0, 0, id=1)], est, cons)
    esperado = 2 * (10 / 60) + 10
    lote = r.lotes[0]
    assert lote.estado == "completado" and lote.fin_min == pytest.approx(esperado)
    assert len(r.tareas) == 2 and all(t.atendida for t in r.tareas)
    assert sum(t.distancia_m for t in r.tareas) == pytest.approx(20)


def test_paralelismo_por_puestos():
    est, cons = red_lineal(puestos=2)
    ped = [Pedido(1, 1, 20, 3, 0, 0, id=1)]
    r2 = correr(ped, est, cons)
    est1, _ = red_lineal(puestos=1)
    r1 = correr(ped, est1, cons)
    fin2 = max(l.fin_min for l in r2.lotes)
    fin1 = max(l.fin_min for l in r1.lotes)
    assert fin1 - fin2 == pytest.approx(10, abs=0.5)


def test_cola_y_utilizacion_de_la_estacion():
    est, cons = red_lineal(puestos=1)
    r = correr([Pedido(1, 1, 30, 3, 0, 0, id=1)], est, cons)
    e = analisis.analizar_estaciones(r, est)[0]
    assert e.cola_max == 2 and e.lotes == 3
    assert e.utilizacion_pct == pytest.approx(30 / 120 * 100)
    assert e.espera_prom_min > 5


def test_cierre_de_turno_deja_lotes_en_curso():
    est, cons = red_lineal()
    r = correr([Pedido(1, 1, 100, 3, 0, 0, id=1)], est, cons, prm(tiempo_observacion_min=30))
    assert any(l.estado == "en curso" for l in r.lotes)
    assert not any(v.inicio_min is not None and v.inicio_min >= 30 for v in r.visitas)


def test_prioridad_adelanta_al_pedido_urgente():
    est, cons = red_lineal()
    pedidos = [Pedido(1, 1, 50, 5, 0, 0, id=1), Pedido(1, 1, 10, 1, 0.01, 0, id=2)]
    prio = correr(pedidos, est, cons, prm(politica="PRIORIDAD"))
    fifo = correr(pedidos, est, cons, prm(politica="FIFO"))
    fin = lambda r, pid: max(l.fin_min for l in r.lotes if l.pedido_id == pid)
    assert fin(prio, 2) < fin(fifo, 2)


def test_viajes_segun_capacidad():
    est, cons = red_lineal()
    r = correr([Pedido(1, 1, 10, 3, 0, 0, id=1)], est, cons, prm(capacidad_kg=12), peso=3.0)
    assert [t.viajes for t in r.tareas] == [3, 3]


def test_carga_mayor_que_capacidad_se_rechaza():
    est, cons = red_lineal()
    r = correr([Pedido(1, 1, 10, 3, 0, 0, id=1)], est, cons, prm(capacidad_kg=1), peso=3.0)
    assert r.lotes[0].estado == "fallido" and not r.tareas[0].atendida


def test_ancho_requerido_veta_pasillos():
    est, _ = red_lineal()
    cons = [con("A", "P", 10, 0.9), con("P", "D", 10, 1.5)]
    r = correr([Pedido(1, 1, 10, 3, 0, 0, id=1)], est, cons, prm(ancho_requerido_m=1.3))
    assert r.lotes[0].estado == "fallido"


def test_grupo_reparte_entre_estaciones_si_balancea():
    est = [Estacion(1, "A", "", "ALMACEN", 0, 0, 0, 1), Estacion(1, "X1", "", "PROCESO", 10, 0, 1.0, 1, "G"),
           Estacion(1, "X2", "", "PROCESO", 10, 5, 1.0, 1, "G"), Estacion(1, "D", "", "DESPACHO", 20, 0, 0, 1)]
    cons = [con("A", "X1", 10), con("A", "X2", 11), con("X1", "D", 10), con("X2", "D", 11)]
    ped = [Pedido(1, 1, 60, 3, 0, 0, id=1)]
    on = correr(ped, est, cons, prm(balanceo=True), secuencia="A>@G>D")
    usados = {v.estacion for v in on.visitas}
    assert usados == {"X1", "X2"}
    off = correr(ped, est, cons, prm(balanceo=False), secuencia="A>@G>D")
    assert max(l.fin_min for l in on.lotes) <= max(l.fin_min for l in off.lotes) + 1e-9


def test_variabilidad_con_semilla_es_reproducible():
    est, cons = red_lineal()
    ped = [Pedido(1, 1, 40, 3, 0, 0, id=1)]
    a = correr(ped, est, cons, prm(variabilidad_pct=20, semilla=7))
    b = correr(ped, est, cons, prm(variabilidad_pct=20, semilla=7))
    c = correr(ped, est, cons, prm(variabilidad_pct=20, semilla=8))
    d = correr(ped, est, cons, prm(variabilidad_pct=0, semilla=8))
    fin = lambda r: max(l.fin_min for l in r.lotes)
    assert fin(a) == fin(b) and fin(a) != fin(c)
    assert fin(d) == fin(correr(ped, est, cons, prm(variabilidad_pct=0, semilla=1)))


def test_generar_lotes_reparte_por_fraccion():
    tipo = TipoPrenda("Camisa", 1, 10, 1.0, id=1)
    rutas = [RutaProceso(1, 1, "a", 70, "A>P>D", id=1), RutaProceso(1, 1, "b", 30, "A>D", id=2)]
    lotes, sin = generar_lotes([Pedido(1, 1, 100, 3, 0, 0, id=1), Pedido(1, 9, 5, 3, 0, 0, id=2)], [tipo], rutas, 100.0)
    assert sin == [2]
    por_rama = {}
    for l in lotes:
        por_rama[l.ruta] = por_rama.get(l.ruta, 0) + l.unidades
    assert por_rama == {"a": 70, "b": 30}


def test_carga_ofrecida_analitica():
    est, _ = red_lineal(t_proc=0.6, puestos=2)
    tipo = TipoPrenda("Camisa", 1, 10, 2.0, id=1)
    ruta = RutaProceso(1, 1, "u", 100, "A>P>D", id=1)
    c = analisis.carga_ofrecida(est, [tipo], [ruta], [Pedido(1, 1, 100, 3, 0, 0, id=1)], 480)
    assert c["P"][0] == pytest.approx(100 * 0.6 * 2.0)
    assert c["P"][1] == pytest.approx(120 / (2 * 480) * 100)


def test_trafico_y_rutas_de_nodo():
    est, cons = red_lineal()
    r = correr([Pedido(1, 1, 20, 3, 0, 0, id=1)], est, cons)
    t = analisis.trafico(r)
    assert t.arcos[frozenset(("A", "P"))] >= 2 and t.nodos["P"] >= 2
    rutas = analisis.rutas_de_nodo(r, "P")
    assert rutas[0]["camino"] == ("A", "P", "D") and rutas[0]["unidades"] == 20 and rutas[0]["principal"]
    assert analisis.rutas_de_nodo(r, "P", pedido_id=99) == []
    assert sum(analisis.trafico_hasta(r, 0.0).arcos.values()) < sum(t.arcos.values())


def test_componentes_criticos_incluye_cuello_y_pasillo_angosto():
    est, _ = red_lineal(t_proc=3.0)
    cons = [con("A", "P", 10, 1.0), con("P", "D", 10, 1.5)]
    r = correr([Pedido(1, 1, 150, 3, 0, 0, id=1)], est, cons, prm(tiempo_observacion_min=480))
    estados = analisis.analizar_estaciones(r, est)
    crit = analisis.componentes_criticos(est, cons, estados, analisis.trafico(r), 1.2, 85.0)
    tipos = {c.tipo for c in crit}
    assert {"Cuello de botella", "Pasillo", "Nodo de red"} <= tipos


def test_validar_rutas_exige_almacen_y_despacho():
    est, _ = red_lineal()
    ok = RutaProceso(1, 1, "ok", 100, "A>P>D")
    assert validar_rutas([ok], est) == []
    assert validar_rutas([RutaProceso(1, 1, "x", 100, "P>D")], est)
    assert validar_rutas([RutaProceso(1, 1, "x", 100, "A>Z>D")], est)
    assert validar_rutas([RutaProceso(1, 1, "x", 100, "A>@NADA>D")], est)


def test_normativa_marca_pasillos_y_robot():
    from textilflow.domain.entities import Escenario, Taller
    est, _ = red_lineal()
    cons = [con("A", "P", 10, 0.95), con("P", "D", 10, 1.5)]
    robot = Robot("R", 50, 0.7, 0.8, 0.9, id=1)
    esc = Escenario(1, "S1", "AMR", 1, 480, 0.7, 50, 0, 0, "A", True, 1)
    par = normativa.valores([])
    res = {c.clave + c.estado: c for c in normativa.evaluar(par, Taller("t", 100, 10), est, cons, [esc], [robot])}
    assert "ancho_min_pasillo_mINCUMPLE" in res
    assert "holgura_lateral_robot_mADVERTENCIA" in res and "0.95" in res["holgura_lateral_robot_mADVERTENCIA"].detalle
    assert normativa.ancho_requerido_robot(robot, par) == pytest.approx(0.8 + 2 * 0.25)


def test_parametros_normativos_declaran_fuente_y_verificacion():
    assert all(p.fuente for p in normativa.PARAMETROS_DEFECTO)
    verificados = {p.clave for p in normativa.PARAMETROS_DEFECTO if p.verificado}
    assert verificados == {"ancho_min_pasillo_m", "dist_min_entre_maquinas_m", "area_min_por_trabajador_m2"}
    assert normativa.valores([Parametro("ancho_min_pasillo_m", 1.5)])["ancho_min_pasillo_m"] == 1.5


def test_estadistica_ic95():
    r = estadistica.resumir([10, 12, 14, 16, 18])
    assert r.media == 14 and r.desv == pytest.approx(math.sqrt(10))
    assert r.ic_inf < 14 < r.ic_sup
    assert r.ic_sup - 14 == pytest.approx(2.776 * r.desv / math.sqrt(5), abs=1e-3)
    assert estadistica.resumir([5]).desv is None and estadistica.resumir([]).media is None
