from ...domain.validacion import FAIL, PASS, WARNING
from ..theme import COLOR_ESTADO, ESTADO_ES
from .base import Controlador


class ValidacionController(Controlador):
    def __init__(self, vista, ctx, validacion):
        super().__init__(vista, ctx)
        self._validacion = validacion
        vista.ejecutar_solicitado.connect(self._ejecutar)

    def _ejecutar(self) -> None:
        tid = self._exigir_taller()
        if tid is None:
            return
        h = self._intentar(self._validacion.execute, tid)
        if h is None:
            return
        n = {e: sum(1 for x in h if x.estado == e) for e in (PASS, WARNING, FAIL)}
        if n[FAIL]:
            veredicto = f"✖ El proyecto NO está apto: corrija los {n[FAIL]} hallazgo(s) con FALLA antes de simular o comparar."
        elif n[WARNING]:
            veredicto = f"⚠ Apto con {n[WARNING]} advertencia(s): deben documentarse como limitaciones del estudio."
        else:
            veredicto = "✔ Proyecto apto: todas las verificaciones pasaron."
        orden = {FAIL: 0, WARNING: 1, PASS: 2}
        h = sorted(h, key=lambda x: orden[x.estado])
        self.vista.mostrar(n[PASS], n[WARNING], n[FAIL], veredicto,
                           [[ESTADO_ES[x.estado], x.codigo, x.area, x.mensaje, x.corregir_en] for x in h],
                           [COLOR_ESTADO[x.estado] for x in h])
