from ...application.use_cases.analisis import METRICAS
from ...domain.entities import POLITICAS, TIPOS_ESCENARIO, Escenario
from ..theme import COLOR_NIVEL, NARANJA, ROJO, VERDE, fmt
from .base import Controlador, etiqueta_estacion

PALETA = ["#5CC8FF", "#FF7AC6", "#B6F36A", "#FFD166", "#C49BFF", "#FF9F6B", "#6BE3B2", "#E5484D"]


def filas_alertas(alertas):
    filas = [[a.nivel, a.codigo, a.titulo + (f" · {a.escenario}" if a.escenario else ""), a.detalle] for a in alertas]
    return filas, [COLOR_NIVEL.get(a.nivel) for a in alertas]


class SimulacionController(Controlador):
    def __init__(self, vista, ctx, escenarios, layout, robots, indicadores, simulacion, replicas, parametros):
        super().__init__(vista, ctx)
        self._esc, self._layout, self._robots = escenarios, layout, robots
        self._indicadores, self._simulacion, self._replicas, self._par = indicadores, simulacion, replicas, parametros
        self._ultimas = None
        p = vista.panel
        p.seleccionado.connect(self._cargar)
        p.guardar_solicitado.connect(self._guardar)
        p.eliminar_solicitado.connect(self._eliminar)
        vista.ejecutar_solicitado.connect(lambda _: self._guardar_y_simular())
        vista.replicas_solicitadas.connect(self._ejecutar_replicas)

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        esc = self._esc.listar(tid) if tid else []
        est = self._layout.listar_estaciones(tid) if tid else []
        p = self.vista.panel
        p.set_opciones("nodo_inicial", [(e.codigo, etiqueta_estacion(e)) for e in est])
        p.set_opciones("robot_id", [(None, "— Sin robot —")] + [(r.id, r.nombre) for r in self._robots.listar()])
        filas = []
        for e in esc:
            n = len(self._indicadores.execute(e.id).registros)
            filas.append([e.id, e.nombre, TIPOS_ESCENARIO[e.tipo], e.num_recursos, POLITICAS[e.politica].split(" ")[0],
                          fmt(e.factor_demanda_pct, 0), n if n else "sin simular"])
        p.set_filas(filas, [e.id for e in esc])
        self.vista.set_escenarios_replicas([(e.id, e.nombre) for e in esc])

    def _cargar(self, id_: int) -> None:
        e = self._intentar(self._esc.obtener, id_)
        if e:
            self.vista.panel.set_valores(vars(e), e.id)

    def _desde_formulario(self, d: dict):
        tid = self._exigir_taller()
        if tid is None:
            return None
        return Escenario(tid, d["nombre"], d["tipo"] or "MANUAL", d["num_recursos"], d["tiempo_observacion_min"],
                         d["velocidad_ms"], d["capacidad_kg"], d["t_carga_s"], d["t_descarga_s"],
                         d["nodo_inicial"] or "", d["reposicionamiento"], d["robot_id"],
                         d["politica"] or "PRIORIDAD", d["balanceo"], d["factor_demanda_pct"],
                         d["variabilidad_pct"], d["semilla"], d["id"])

    def _guardar(self, d: dict):
        e = self._desde_formulario(d)
        if e is None:
            return None
        g = self._intentar(self._esc.guardar, e)
        if g:
            self.vista.panel.set_valores(vars(g), g.id)
            self.refrescar()
            self.vista.panel.tabla.seleccionar_id(g.id)
            self.vista.info(f"Escenario «{g.nombre}» guardado.")
        return g

    def _eliminar(self, id_: int) -> None:
        if self.vista.confirmar("¿Eliminar el escenario y sus registros?"):
            self._esc.eliminar(id_)
            self.vista.panel.limpiar()
            self.refrescar()
            self.vista.info("Escenario eliminado.")

    def _guardar_y_simular(self) -> None:
        e = self._guardar(self.vista.panel.valores())
        if e is None:
            return
        r = self._intentar(self._simulacion.execute, e.id)
        if r is None:
            return
        self.refrescar()
        ind, i2 = r.ind, r.indicadores
        umbral = self._par.valores()["umbral_cuello_botella_pct"]
        s = r.series
        wip = (s["t"], [("En el sistema", "#5CC8FF", s["wip"]), ("Completados", "#6BE3B2", s["completados"])])
        paleta = {}
        series_cola = []
        for i, (cod, vals) in enumerate(s["cola"].items()):
            series_cola.append((cod, PALETA[i % len(PALETA)], vals))
        filas, colores = [], []
        for est in r.estados:
            filas.append([f"{est.codigo} · {est.nombre}", est.capacidad, fmt(est.utilizacion_pct, 1),
                          fmt(est.carga_ofrecida_pct, 1), fmt(est.espera_prom_min, 1), fmt(est.espera_max_min, 1),
                          est.cola_max, est.lotes, est.unidades])
            colores.append(ROJO if max(est.utilizacion_pct, est.carga_ofrecida_pct or 0) >= umbral else None)
        fa, ca = filas_alertas(r.alertas)
        self.vista.mostrar_resultados(
            f"SIMULACIÓN COMPLETADA · «{e.nombre}» · {POLITICAS[e.politica]} · {e.num_recursos} recurso(s) · "
            f"{ind.lotes_completados}/{ind.lotes} lotes completados · {len(r.alertas)} alerta(s).",
            [(f"{ind.lotes_completados}/{ind.lotes}", f"{fmt(ind.completados_pct, 1)} % · {ind.unidades_completadas}/{ind.unidades} u"),
             (fmt(ind.makespan_min, 0, " min"), "hasta la última entrega"),
             (fmt(ind.lead_time_prom_min, 0, " min"), "Almacén → Despacho"),
             (fmt(ind.pedidos_a_tiempo_pct, 0, " %"), "de los pedidos con límite"),
             (fmt(i2["espera_prom"], 2, " min"), "promedio por traslado"),
             (fmt(i2["utilizacion_pct"], 1, " %"), f"de {e.num_recursos} recurso(s)")],
            wip, (s["t"], series_cola), filas, colores, fa, ca)
        self.vista.g_wip.set_marca(None)

    def _ejecutar_replicas(self, escenario_id: int, n: int) -> None:
        r = self._intentar(self._replicas.execute, escenario_id, n)
        if r is None:
            return
        self._ultimas = r
        stats = []
        for k, (nombre, dec) in METRICAS.items():
            x = r.resumen[k]
            stats.append([nombre, x.n, fmt(x.media, dec), fmt(x.desv, dec), fmt(x.minimo, dec), fmt(x.maximo, dec),
                          fmt(x.ic_inf, dec), fmt(x.ic_sup, dec)])
        runs = [[f["semilla"], fmt(f["makespan_min"], 1), fmt(f["lead_time_min"], 1), fmt(f["completados_pct"], 1),
                 fmt(f["a_tiempo_pct"], 0), fmt(f["espera_traslado_min"], 2), fmt(f["utilizacion_flota_pct"], 1),
                 f["cola_max"]] for f in r.filas]
        self.vista.mostrar_replicas(r.nota or f"{r.n} réplicas de «{r.escenario.nombre}» · variabilidad ± "
                                    f"{r.escenario.variabilidad_pct:g} % · semillas {r.filas[0]['semilla']}–{r.filas[-1]['semilla']}.",
                                    stats, runs, *self._estabilidad(r))

    def _estabilidad(self, r):
        filas, todas_iguales = [], True
        for k, (nombre, dec) in METRICAS.items():
            x = r.resumen[k]
            if x.media is None:
                continue
            cv = None if not x.media else (x.desv or 0) / abs(x.media) * 100
            if x.desv:
                todas_iguales = False
            # umbrales a ojo, solo para dar una idea rápida
            if cv is None or cv < 0.05:
                nivel, color = "Siempre igual", VERDE
            elif cv < 3:
                nivel, color = "Muy estable", VERDE
            elif cv < 8:
                nivel, color = "Algo variable", NARANJA
            else:
                nivel, color = "Muy variable", ROJO
            filas.append((nombre, fmt(x.media, dec), f"entre {fmt(x.minimo, dec)} y {fmt(x.maximo, dec)}", nivel, color,
                          min((cv or 0) / 10, 1.0)))
        if todas_iguales:
            msg = ("Las réplicas dieron todas lo mismo porque la variabilidad del escenario es 0 %. "
                   "Pruebe con 10 o 15 % en «Condiciones base» para ver cuánto cambia el resultado.")
        else:
            msg = ("La barra mide cuánto se mueve cada resultado de una réplica a otra: "
                   "cuanto más corta, más confiable es el número.")
        return filas, msg
