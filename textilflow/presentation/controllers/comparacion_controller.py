from ..textos import DECIMALES, FORMULA_VARIACION, MEJOR_SI_BAJA
from ..theme import AZUL, ROJO, TENUE, VERDE, fmt
from ..widgets.bar_chart import BarraVariacion
from .base import Controlador


def color_variacion(clave: str, v) -> str:
    """Verde si el cambio es una mejora, rojo si empeora, gris si es neutro o no hay dato."""
    mejor_si_baja = MEJOR_SI_BAJA.get(clave)
    if v is None or mejor_si_baja is None or v == 0:
        return TENUE
    return VERDE if (v < 0) == mejor_si_baja else ROJO


def texto_variacion(v) -> str:
    return "n/d" if v is None else f"{v:+.1f} %"


class ComparacionController(Controlador):
    def __init__(self, vista, ctx, escenarios, comparacion):
        super().__init__(vista, ctx)
        self._esc, self._cmp = escenarios, comparacion
        vista.barra.ejecutar.connect(self._comparar)

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        esc = self._esc.listar(tid) if tid else []
        self.vista.barra.set_escenarios([(e.id, e.nombre) for e in esc])

    def _comparar(self, base_id: int, alt_id: int) -> None:
        r = self._intentar(self._cmp.execute, base_id, alt_id)
        if r is None:
            return
        filas = [[f["indicador"], fmt(f["base"], DECIMALES[f["clave"]]), fmt(f["alternativo"], DECIMALES[f["clave"]]),
                  texto_variacion(f["variacion_pct"])] for f in r.filas]
        barras = [BarraVariacion(f["indicador"], f["variacion_pct"], color_variacion(f["clave"], f["variacion_pct"]))
                  for f in r.filas]
        if r.comparable:
            veredicto = (f"✔ Escenarios comparables · Base: «{r.base.nombre}» · Alternativo: «{r.alternativo.nombre}» · "
                         f"{FORMULA_VARIACION}")
        else:
            veredicto = "✖ No comparables: " + " ".join(r.problemas)
        proceso = [[f["indicador"], fmt(f["base"], 1), fmt(f["alternativo"], 1), texto_variacion(f["variacion_pct"])]
                   for f in r.filas_proceso]
        avance = None
        if r.series_base and r.series_alt:
            avance = (r.series_base["t"], [(r.base.nombre, "#8FA0BC", r.series_base["completados"]),
                                           (r.alternativo.nombre, "#6BE3B2", r.series_alt["completados"])])
        self.vista.mostrar(veredicto, filas, barras, proceso, avance)
