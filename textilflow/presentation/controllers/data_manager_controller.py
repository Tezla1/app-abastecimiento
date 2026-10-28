from datetime import datetime

from .base import Controlador


class DataManagerController(Controlador):
    def __init__(self, vista, ctx, datos, demo):
        super().__init__(vista, ctx)
        self._datos, self._demo = datos, demo
        vista.plantilla_solicitada.connect(lambda r: self._hacer(
            lambda: self._datos.crear_plantilla(r), f"Plantilla creada en {r}"))
        vista.importar_solicitado.connect(self._importar)
        vista.exportar_solicitado.connect(self._exportar)
        vista.exportar_proyecto_solicitado.connect(lambda r: self._hacer(
            lambda: self._datos.exportar_proyecto(r), f"Proyecto exportado a {r}"))
        vista.restaurar_solicitado.connect(self._restaurar)
        vista.demo_solicitado.connect(self._cargar_demo)
        vista.ejemplo_archivo_solicitado.connect(lambda r: self._importar(r, con_escenario=True))

    def _hacer(self, accion, mensaje: str) -> bool:
        try:
            accion()
        except Exception as e:  # el error de archivo (permisos, disco) tampoco debe tumbar la app
            from ...application.errors import ErrorDeNegocio
            texto = str(e) if isinstance(e, ErrorDeNegocio) else f"No se pudo completar la operación: {e}"
            self.vista.info(f"[{datetime.now():%H:%M:%S}] ✖ {texto}")
            self.vista.error(texto)
            return False
        self.vista.info(f"[{datetime.now():%H:%M:%S}] ✔ {mensaje}")
        return True

    def _exportar(self, ruta: str) -> None:
        tid = self._exigir_taller()
        if tid is not None:
            self._hacer(lambda: self._datos.exportar_taller(tid, ruta), f"Taller exportado a {ruta}")

    def _importar(self, ruta: str, con_escenario: bool = False) -> None:
        resultado = {}

        def accion():
            resultado["t"], resultado["msg"] = self._datos.importar_taller(ruta)

        if self._hacer(accion, "Archivo validado."):
            self.vista.info(resultado["msg"])
            if con_escenario and self._demo.preparar_escenario_base(resultado["t"]):
                self.vista.info("Se creó el escenario base S0 · Manual (2 operarios) y se simuló.")
            self.ctx.talleres_cambiaron.emit()
            self.ctx.activar(resultado["t"].id)

    def _restaurar(self, ruta: str) -> None:
        if self._hacer(lambda: self._datos.restaurar_proyecto(ruta), f"Proyecto restaurado desde {ruta}"):
            self.ctx.activar(None)
            self.ctx.talleres_cambiaron.emit()

    def _cargar_demo(self) -> None:
        resultado = {}
        if self._hacer(lambda: resultado.setdefault("t", self._demo.execute()), "Datos de ejemplo cargados."):
            self.ctx.talleres_cambiaron.emit()
            self.ctx.activar(resultado["t"].id)
