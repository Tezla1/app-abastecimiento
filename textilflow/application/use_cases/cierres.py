# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Cierres de área: crearlos y editarlos, medir su impacto con y sin cierre, y exportar el informe de contingencias.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ...domain import analisis
from ...domain.entities import MOTIVOS_CIERRE, Cierre
from ..errors import ErrorDeNegocio
from ..ports import CierreRepository, EscenarioRepository, EstacionRepository, ExportadorReportes
from .contexto import CargadorContexto
from .nucleo import analizar, correr, exigir_simulable
from .talleres import exigir_valido


class GestionarCierres:
    def __init__(self, cierres: CierreRepository, estaciones: EstacionRepository):
        self._cie, self._est = cierres, estaciones

    def listar(self, taller_id: int) -> list[Cierre]:
        return sorted(self._cie.list_by_taller(taller_id), key=lambda c: c.id or 0)

    def nombres(self, taller_id: int) -> dict:
        return {e.codigo: e.nombre or e.codigo for e in self._est.list_by_taller(taller_id)}

    def cerrados(self, taller_id: Optional[int]) -> frozenset:
        if taller_id is None:
            return frozenset()
        return frozenset(c.codigo for c in self.listar(taller_id) if c.vigente)

    def guardar(self, c: Cierre) -> Cierre:
        exigir_valido(c)
        est = next((e for e in self._est.list_by_taller(c.taller_id) if e.codigo == c.codigo), None)
        if est is None:
            raise ErrorDeNegocio(f"El área «{c.codigo}» no existe en este taller.")
        if est.funcion in ("ALMACEN", "DESPACHO"):
            raise ErrorDeNegocio("No se puede cerrar el Almacén ni el Despacho: son el inicio y el fin de todas las rutas.")
        if c.id is None:
            c.registrado = datetime.now().strftime("%Y-%m-%d %H:%M")
            return self._cie.add(c)
        return self._cie.update(c)

    def cambiar_vigencia(self, cierre_id: int, vigente: bool) -> Cierre:
        c = self._cie.get(cierre_id)
        if c is None:
            raise ErrorDeNegocio("El cierre ya no existe.")
        c.vigente = vigente
        return self._cie.update(c)

    def eliminar(self, cierre_id: int) -> None:
        self._cie.delete(cierre_id)


@dataclass
class InformeCierre:
    escenario: object
    cierres: list
    nivel: str
    resumen: str
    indicadores: list
    estaciones: list
    reasignaciones: list
    rutas: list
    afectados: list
    alertas_nuevas: list
    recomendaciones: list
    generado: str = ""


def _variacion(antes, ahora):
    if antes in (None, 0) or ahora is None:
        return None
    return (ahora - antes) / abs(antes) * 100


class InformeCierres:
    def __init__(self, escenarios: EscenarioRepository, ctx: CargadorContexto):
        self._esc, self._ctx = escenarios, ctx

    def execute(self, escenario_id: int) -> InformeCierre:
        esc = self._esc.get(escenario_id)
        if esc is None:
            raise ErrorDeNegocio("Seleccione un escenario guardado.")
        ctx = self._ctx.cargar(esc.taller_id)
        exigir_simulable(ctx)
        if not ctx.vigentes():
            raise ErrorDeNegocio("No hay cierres vigentes en este taller: cierre un área para generar el informe.")
        antes = analizar(ctx.sin_cierres(), esc, correr(ctx.sin_cierres(), esc))
        ahora = analizar(ctx, esc, correr(ctx, esc))
        nombres = {e.codigo: e.nombre or e.codigo for e in ctx.estaciones}
        i0, i1 = antes.ind, ahora.ind
        c0, c1 = antes.indicadores, ahora.indicadores

        indicadores = []
        for nombre, a, b, mejor_si_baja, dec in [
                ("Lotes completados (%)", i0.completados_pct, i1.completados_pct, False, 1),
                ("Unidades completadas", i0.unidades_completadas, i1.unidades_completadas, False, 0),
                ("Cierre de la última entrega (min)", i0.makespan_min, i1.makespan_min, True, 0),
                ("Tiempo medio de un lote (min)", i0.lead_time_prom_min, i1.lead_time_prom_min, True, 0),
                ("Pedidos entregados a tiempo (%)", i0.pedidos_a_tiempo_pct, i1.pedidos_a_tiempo_pct, False, 0),
                ("Distancia recorrida por el transporte (m)", c0.get("distancia_total"), c1.get("distancia_total"), True, 0),
                ("Utilización de la flota (%)", c0.get("utilizacion_pct"), c1.get("utilizacion_pct"), None, 1)]:
            v = _variacion(a, b)
            if mejor_si_baja and i0.completados_pct - i1.completados_pct > 0.5:
                mejor_si_baja = None
            if v is None or abs(v) < 0.05 or mejor_si_baja is None:
                estado = "igual" if v is None or abs(v) < 0.05 else "cambia"
            else:
                estado = "mejora" if (v < 0) == mejor_si_baja else "empeora"
            indicadores.append((nombre, a, b, v, estado, dec))

        e0 = {s.codigo: s for s in antes.estados}
        estaciones = []
        for s in ahora.estados:
            a = e0.get(s.codigo)
            if a is None:
                continue
            estaciones.append((f"{s.codigo} · {s.nombre}", a.lotes, s.lotes, a.utilizacion_pct, s.utilizacion_pct,
                               a.cola_max, s.cola_max, s.codigo in {c.codigo for c in ctx.vigentes()}))

        grupos = {}
        for c in ctx.vigentes():
            e = next((x for x in ctx.estaciones if x.codigo == c.codigo), None)
            if e and e.grupo:
                grupos.setdefault(e.grupo, []).append(c.codigo)
        reasignaciones = []
        for g, cerrados in grupos.items():
            for s in ahora.estados:
                e = next((x for x in ctx.estaciones if x.codigo == s.codigo), None)
                if e and e.grupo == g:
                    a = e0[s.codigo]
                    reasignaciones.append((g, f"{s.codigo} · {s.nombre}", a.lotes, s.lotes, a.unidades, s.unidades,
                                           s.codigo in cerrados))

        vel, ancho = esc.velocidad_ms, 0.0
        ramas0 = analisis.distancias_ramas(ctx.estaciones, ctx.conexiones, ctx.tipos, ctx.rutas, vel, ancho)
        ramas1 = analisis.distancias_ramas(ctx.estaciones, ctx.conexiones, ctx.tipos, ctx.rutas, vel, ancho,
                                           ctx.cerrados(), ctx.sin_paso())
        rutas = []
        for r0, r1 in zip(ramas0, ramas1):
            if r0.pasos != r1.pasos or r0.alcanzable != r1.alcanzable:
                rutas.append((r0.prenda, r0.ruta, " → ".join(r0.pasos),
                              " → ".join(r1.pasos) if r1.alcanzable else "sin camino posible",
                              r0.distancia_m, r1.distancia_m if r1.alcanzable else None, r1.alcanzable))

        afectados = {}
        for l in ahora.proceso.lotes:
            if l.estado == "completado":
                continue
            clave = (l.prenda, l.pedido_id, l.estado, l.motivo)
            fila = afectados.setdefault(clave, [0, 0])
            fila[0] += 1
            fila[1] += l.unidades
        lista_afectados = sorted(((p, pid, est, mot, n, u) for (p, pid, est, mot), (n, u) in afectados.items()),
                                 key=lambda x: (-x[5], x[1]))

        previas = {(a.codigo, a.elemento) for a in antes.alertas}
        nuevas = [a for a in ahora.alertas if (a.codigo, a.elemento) not in previas]

        caida = i0.completados_pct - i1.completados_pct
        if caida >= 15 or i1.lotes_fallidos >= max(3, 0.1 * i1.lotes):
            nivel = "ALTO"
        elif caida >= 5 or i1.lotes_fallidos or (i1.makespan_min - i0.makespan_min) > 30:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"

        cerr = [dict(codigo=c.codigo, nombre=nombres.get(c.codigo, c.codigo), motivo=MOTIVOS_CIERRE.get(c.motivo, c.motivo),
                     detalle=c.detalle, desde=c.desde_min, hasta=c.hasta_min, bloquea_paso=c.bloquea_paso,
                     registrado=c.registrado) for c in ctx.vigentes()]
        quienes = ", ".join(f"«{c['nombre']}»" for c in cerr)
        resumen = (f"Con {quienes} fuera de servicio, se completan {i1.lotes_completados} de {i1.lotes} lotes "
                   f"({i1.completados_pct:.1f} %) frente a {i0.lotes_completados} de {i0.lotes} sin el cierre "
                   f"({i0.completados_pct:.1f} %). La última entrega pasa de {i0.makespan_min:.0f} a {i1.makespan_min:.0f} min. "
                   f"Impacto {nivel.lower()}.")

        recs = []
        cuello0 = analisis.cuello_de_botella(antes.estados, ctx.par["umbral_cuello_botella_pct"])
        cuello1 = analisis.cuello_de_botella(ahora.estados, ctx.par["umbral_cuello_botella_pct"])
        for g, cerrados in grupos.items():
            restantes = [s for s in ahora.estados
                         if next((x.grupo for x in ctx.estaciones if x.codigo == s.codigo), "") == g
                         and s.codigo not in cerrados]
            if restantes:
                peor = max(restantes, key=lambda s: s.utilizacion_pct)
                recs.append(f"El trabajo de «{', '.join(nombres[c] for c in cerrados)}» pasó a "
                            f"{', '.join(nombres[s.codigo] for s in restantes)}; la más cargada queda al "
                            f"{peor.utilizacion_pct:.0f} % de utilización."
                            + (" Conviene reforzar con personal o puestos adicionales." if peor.utilizacion_pct >= 85 else ""))
            else:
                recs.append(f"El grupo «{g}» quedó sin áreas disponibles: ningún lote puede pasar por ese paso.")
        sin_alt = [r for r in rutas if not r[6]]
        if sin_alt:
            recs.append(f"{len(sin_alt)} ruta(s) quedan sin camino posible; defina una ruta alternativa o un área de respaldo "
                        "para esos pasos.")
        if i1.lotes_fallidos:
            recs.append(f"{i1.lotes_fallidos} lote(s) no se pudieron procesar. Prioridad: recuperar el área o reasignar esos pedidos.")
        if cuello1 and (not cuello0 or cuello0.codigo != cuello1.codigo):
            recs.append(f"El cuello de botella pasa a ser «{cuello1.nombre or cuello1.codigo}»"
                        + (f" (antes «{cuello0.nombre or cuello0.codigo}»)." if cuello0 else "."))
        if any(c["hasta"] == 0 for c in cerr):
            recs.append("El cierre no tiene hora de reapertura: si la reparación tiene fecha estimada, regístrela para ver cuánto se recupera.")
        if not recs:
            recs.append("El impacto es pequeño: el resto del taller absorbe el trabajo sin problemas.")

        return InformeCierre(esc, cerr, nivel, resumen, indicadores, estaciones, reasignaciones, rutas,
                             lista_afectados, nuevas, recs, datetime.now().strftime("%Y-%m-%d %H:%M"))


class ExportarContingencias:
    def __init__(self, cierres: GestionarCierres, informe: InformeCierres, exportador: ExportadorReportes):
        self._cie, self._inf, self._exp = cierres, informe, exportador

    def execute(self, taller_id: int, escenario_id: int, ruta: str) -> int:
        lista = self._cie.listar(taller_id)
        if not lista:
            raise ErrorDeNegocio("No hay contingencias registradas para exportar.")
        nombres = self._cie.nombres(taller_id)
        cierres = [{"Fecha y hora": c.registrado or "—", "Código": c.codigo, "Área": nombres.get(c.codigo, c.codigo),
                    "Motivo": MOTIVOS_CIERRE.get(c.motivo, c.motivo), "Detalle": c.detalle or "—",
                    "Desde (min)": c.desde_min, "Reabre (min)": c.hasta_min if c.hasta_min else "no reabre",
                    "Bloquea el paso": "Sí" if c.bloquea_paso else "No",
                    "Estado": "Cerrada" if c.vigente else "Reabierta"} for c in lista]
        rutas = []
        if escenario_id and any(c.vigente for c in lista):
            for pr, r, a, b, d0, d1, ok in self._inf.execute(escenario_id).rutas:
                rutas.append({"Prenda": pr, "Rama": r, "Ruta normal": a, "Ruta alternativa": b,
                              "Metros antes": round(d0, 1), "Metros ahora": round(d1, 1) if ok else None})
        self._exp.exportar_contingencias(ruta, f"Contingencias · generado {datetime.now():%Y-%m-%d %H:%M}", cierres, rutas)
        return len(cierres)
