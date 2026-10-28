# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Controlador de Resultados y reportes: resumen comparativo y exportación a Excel.

from ..textos import DECIMALES, FORMULA_VARIACION, MEJOR_SI_BAJA
from ..theme import fmt
from .base import Controlador
from .comparacion_controller import texto_variacion


def _lectura(f: dict) -> str:
    v, clave = f["variacion_pct"], f["clave"]
    if v is None:
        return f"{f['indicador']}: sin datos suficientes para calcular la variación."
    if v == 0:
        return f"{f['indicador']}: sin cambio."
    sube = v > 0
    mejor_si_baja = MEJOR_SI_BAJA.get(clave)
    juicio = "" if mejor_si_baja is None else (" (mejora)" if sube != mejor_si_baja else " (empeora)")
    return f"{f['indicador']}: {'aumenta' if sube else 'disminuye'} {abs(v):.1f} %{juicio}."


class ResultadosController(Controlador):
    def __init__(self, vista, ctx, escenarios, comparacion, reporte):
        super().__init__(vista, ctx)
        self._esc, self._cmp, self._reporte = escenarios, comparacion, reporte
        vista.barra.ejecutar.connect(self._informe)
        vista.exportar_solicitado.connect(self._exportar)

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        esc = self._esc.listar(tid) if tid else []
        self.vista.barra.set_escenarios([(e.id, e.nombre) for e in esc])

    def _informe(self, base_id: int, alt_id: int) -> None:
        r = self._intentar(self._cmp.execute, base_id, alt_id)
        if r is None:
            return
        lineas = ["INFORME DE COMPARACIÓN DE ESCENARIOS", "=" * 40,
                  f"Base (S0):        {r.base.nombre} · {r.base.num_recursos} recurso(s)",
                  f"Alternativo (S1): {r.alternativo.nombre} · {r.alternativo.num_recursos} recurso(s)",
                  f"Comparable:       {'Sí' if r.comparable else 'NO — ' + ' '.join(r.problemas)}",
                  f"Fórmula:          {FORMULA_VARIACION}", "",
                  f"{'Indicador':<44}{'Base':>12}{'Alternativo':>14}{'Variación':>12}", "-" * 82]
        for f in r.filas:
            d = DECIMALES[f["clave"]]
            lineas.append(f"{f['indicador']:<44}{fmt(f['base'], d):>12}{fmt(f['alternativo'], d):>14}"
                          f"{texto_variacion(f['variacion_pct']):>12}")
        if r.filas_proceso:
            lineas += ["", "Indicadores del proceso completo (Almacén → Despacho):", "-" * 82]
            for f in r.filas_proceso:
                lineas.append(f"{f['indicador']:<44}{fmt(f['base'], 1):>12}{fmt(f['alternativo'], 1):>14}"
                              f"{texto_variacion(f['variacion_pct']):>12}")
        lineas += ["", "Lectura:"] + [f"  • {_lectura(f)}" for f in r.filas]
        self.vista.mostrar_informe("\n".join(lineas))
        self.vista.info("Informe generado." if r.comparable else "Informe generado, pero los escenarios no son comparables.")

    def _exportar(self, base_id: int, alt_id: int, ruta: str, formato: str) -> None:
        ok = self._intentar(lambda: self._reporte.execute(base_id, alt_id, ruta, formato) or True)
        if ok:
            self.vista.info(f"Reporte exportado a {ruta}")
