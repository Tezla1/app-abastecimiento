# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Controlador del Data Manager: importar y exportar Excel, proyecto .rlr, respaldos y datos de ejemplo.

from datetime import datetime

from ... import registro

from .base import Controlador


class DataManagerController(Controlador):
    def __init__(self, vista, ctx, datos, demo, respaldos=None):
        super().__init__(vista, ctx)
        self._datos, self._demo, self._respaldos = datos, demo, respaldos
        vista.respaldos_solicitados.connect(self._respaldos_auto)
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
        except Exception as e:
            from ...application.errors import ErrorDeNegocio
            if isinstance(e, ErrorDeNegocio):
                texto = str(e)
            else:
                d = registro.describir(type(e), e, e.__traceback__)
                registro.registrar("Falló una operación del Data Manager", e)
                texto = f"{d['titulo']}: {d['que']} (Dónde: {d['donde']}. Técnico: {d['resumen']})"
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

    def _respaldos_auto(self) -> None:
        lista = self._respaldos.listar() if self._respaldos else []
        if not lista:
            self.vista.info("Todavía no hay respaldos automáticos (se crean cada 5 minutos si hay cambios, y al cerrar).")
            self.vista.error("Todavía no hay respaldos automáticos.")
            return
        etiquetas = [f"{f:%d/%m/%Y %H:%M:%S}" for _, f in lista]
        i = self.vista.elegir_respaldo(etiquetas)
        if i < 0 or not self.vista.confirmar("Esto reemplazará TODOS los datos actuales por los de ese respaldo. ¿Continuar?"):
            return
        self._restaurar(str(lista[i][0]))

    def _restaurar(self, ruta: str) -> None:
        if self._hacer(lambda: self._datos.restaurar_proyecto(ruta), f"Proyecto restaurado desde {ruta}"):
            self.ctx.activar(None)
            self.ctx.talleres_cambiaron.emit()

    def _cargar_demo(self) -> None:
        resultado = {}
        if self._hacer(lambda: resultado.setdefault("t", self._demo.execute()), "Datos de ejemplo cargados."):
            self.ctx.talleres_cambiaron.emit()
            self.ctx.activar(resultado["t"].id)
