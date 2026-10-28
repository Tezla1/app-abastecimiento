from ...domain.normativa import CUMPLE, INCUMPLE
from ..theme import COLOR_NIVEL, NARANJA, ROJO, TENUE, VERDE, fmt
from .base import Controlador
from .simulacion_controller import filas_alertas

SEV = {"CRÍTICA": ROJO, "ALTA": NARANJA, "MEDIA": "#D9A21B"}
ESTADO_COLOR = {CUMPLE: VERDE, INCUMPLE: ROJO}


class RequerimientosController(Controlador):
    def __init__(self, vista, ctx, escenarios, requerimientos, alertas, parametros):
        super().__init__(vista, ctx)
        self._esc, self._req, self._alertas, self._par = escenarios, requerimientos, alertas, parametros
        self._lista = []
        vista.analizar_solicitado.connect(self._analizar)
        vista.guardar_parametro.connect(self._guardar_parametro)
        vista.restaurar_parametros.connect(self._restaurar)
        vista.parametro_elegido.connect(self._parametro_elegido)

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        esc = self._esc.listar(tid) if tid else []
        self.vista.set_escenarios([(e.id, e.nombre) for e in esc])
        self._mostrar_parametros()
        if tid:
            fa, ca = filas_alertas(self._intentar(self._alertas.execute, tid) or [])
            self.vista.t_alertas.set_filas(fa, colores=ca)
        else:
            self.vista.t_alertas.set_filas([])

    def _mostrar_parametros(self) -> None:
        self._lista = self._par.listar()
        self.vista.t_params.set_filas(
            [[p.clave, f"{p.valor:g}", p.unidad, p.descripcion, p.fuente, "Sí" if p.verificado else "No"] for p in self._lista],
            colores=[None if p.verificado else TENUE for p in self._lista])
        self.vista.set_parametros([(p.clave, f"{p.clave} ({p.unidad})") for p in self._lista])
        self._parametro_elegido(self.vista.combo_param.currentData() or "")

    def _parametro_elegido(self, clave: str) -> None:
        p = next((x for x in self._lista if x.clave == clave), None)
        if p:
            self.vista.valor_param.setValue(p.valor)

    def _guardar_parametro(self, clave: str, valor: float) -> None:
        if self._intentar(self._par.cambiar_valor, clave, valor):
            self._mostrar_parametros()
            self.vista.info(f"Parámetro «{clave}» actualizado. Vuelva a analizar para aplicarlo.")

    def _restaurar(self) -> None:
        if self.vista.confirmar("¿Restaurar todos los parámetros a sus valores por defecto?"):
            self._par.restaurar()
            self._mostrar_parametros()
            self.vista.info("Parámetros restaurados.")

    def _analizar(self, escenario_id: int, n_max: int) -> None:
        if not escenario_id:
            self.vista.error("Cree un escenario en «Escenarios y simulación» primero.")
            return
        r = self._intentar(self._req.execute, escenario_id, n_max)
        if r is None:
            return
        v = self.vista
        v.t_criticos.set_filas([[c.severidad, c.tipo, c.elemento, c.motivo] for c in r.criticos],
                               colores=[SEV.get(c.severidad) for c in r.criticos])
        v.t_ramas.set_filas([[x.prenda, x.ruta, fmt(x.fraccion_pct, 0), "→".join(x.pasos),
                              fmt(x.distancia_m, 1) if x.alcanzable else "sin camino",
                              fmt(x.tiempo_transporte_min, 1) if x.alcanzable else "—"] for x in r.ramas],
                            colores=[None if x.alcanzable else ROJO for x in r.ramas])
        rc = r.recorridos
        v.lbl_recorridos.setText(
            f"Turno simulado: {rc['viajes']} viajes cargados para {rc['traslados']} traslados · distancia cargada "
            f"{fmt(rc['distancia_cargada_m'], 0)} m + vacía {fmt(rc['distancia_vacia_m'], 0)} m = {fmt(rc['distancia_total_m'], 0)} m.")
        v.t_recursos.set_filas([[f"Recurso {k}", d["viajes"], fmt(d["distancia_m"], 0), fmt(d["ocupado_min"], 1)]
                                for k, d in sorted(rc["por_recurso"].items())])
        objetivo = next((p.valor for p in self._lista if p.clave == "utilizacion_objetivo_flota_pct"), 75)
        v.k_reco.set_valor(str(r.recomendado) if r.recomendado else "—",
                           f"con utilización ≤ {objetivo:g} %" if r.recomendado else "ninguna flota lo logra")
        v.k_anal.set_valor(str(r.flota["equipos"]), f"{fmt(r.flota['trabajo_min'], 0)} min de transporte / turno")
        v.k_viajes.set_valor(str(rc["viajes"]), f"{rc['traslados']} traslados")
        v.k_dist.set_valor(fmt(rc["distancia_total_m"], 0, " m"), "cargado + vacío")
        v.t_barrido.set_filas([[f.recursos, fmt(f.utilizacion_pct, 1), fmt(f.espera_prom_min, 2), fmt(f.completados_pct, 1),
                                fmt(f.lead_time_min, 0), fmt(f.makespan_min, 0), fmt(f.a_tiempo_pct, 0), "✔" if f.cumple else ""]
                               for f in r.barrido],
                              colores=[VERDE if f.cumple else None for f in r.barrido])
        v.g_barrido.set_datos([(f"{f.recursos} equipo{'s' if f.recursos != 1 else ''}", f.utilizacion_pct or 0,
                                f"termina {f.completados_pct:.0f} % de lotes", f.recursos == r.recomendado)
                               for f in r.barrido], objetivo)
        v.t_viajes.set_filas([[x["prenda"], fmt(x["peso_unidad_kg"], 2), x["lote_u"], fmt(x["lote_kg"], 1),
                               x["unidades_por_viaje"], x["viajes_por_traslado"] if x["viajes_por_traslado"] else "no carga",
                               x["lotes"], x["traslados_por_lote"], x["viajes_estimados"] if x["viajes_estimados"] else "—"]
                              for x in r.viajes_por_prenda])
        v.notas.setText("\n".join("• " + n for n in r.notas))
        v.t_norma.set_filas([[c.estado, c.regla, c.detalle, c.fuente, "Sí" if c.verificado else "No"] for c in r.cumplimientos],
                            colores=[ESTADO_COLOR.get(c.estado, NARANJA) for c in r.cumplimientos])
        n_crit = sum(1 for c in r.criticos if c.severidad in ("CRÍTICA", "ALTA"))
        v.resumen.setText(
            f"«{r.escenario.nombre}» · {len(r.criticos)} componente(s) crítico(s) ({n_crit} de severidad alta o crítica) · "
            f"flota recomendada: {r.recomendado or '—'} · {sum(1 for c in r.cumplimientos if c.estado == INCUMPLE)} incumplimiento(s) normativo(s).")
        v.info("Análisis completado.")
