# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Controlador del Modelo matemático: muestra variables, fórmulas e indicadores de cada escenario.

from ...domain.calculos import ETIQUETAS
from ..textos import DECIMALES, FORMULAS
from ..theme import NARANJA, ROJO, fmt
from .base import Controlador


class ModeloController(Controlador):
    def __init__(self, vista, ctx, escenarios, indicadores, simulacion, parametros):
        super().__init__(vista, ctx)
        self._escenarios = escenarios
        self._indicadores = indicadores
        self._simulacion = simulacion
        self._par = parametros
        vista.calcular_solicitado.connect(self._calcular)

    def refrescar(self) -> None:
        tid = self.ctx.taller_id
        esc = self._escenarios.listar(tid) if tid else []
        self.vista.set_escenarios([(e.id, e.nombre) for e in esc])

    def _calcular(self, escenario_id: int) -> None:
        r = self._intentar(self._indicadores.execute, escenario_id)
        if r is None:
            return
        ind = r.indicadores
        filas = [[nombre, fmt(ind.get(clave), DECIMALES[clave]), FORMULAS[clave]] for clave, nombre in ETIQUETAS.items()]
        if not r.registros:
            resumen = (f"«{r.escenario.nombre}» no tiene registros: ejecute la simulación (Escenarios y simulación) "
                       "para generar los traslados que alimentan el modelo.")
        else:
            resumen = (f"«{r.escenario.nombre}» · {ind['n_registros']} traslados, {ind['n_atendidas']} atendidos · "
                       f"{r.escenario.num_recursos} recurso(s) · observación {r.escenario.tiempo_observacion_min:g} min.")
        filas_reg = [[x.pedido_id, x.lote, f"{x.desde} → {x.hacia}", "Sí" if x.atendida else "No", fmt(x.tiempo_espera_min),
                      fmt(x.tiempo_recorrido_min), fmt(x.distancia_m, 1), x.viajes, x.detalle] for x in r.registros]
        rho_filas, rho_col = [], []
        sim = self._intentar(self._simulacion.execute, escenario_id, False) if r.registros else None
        if sim:
            umbral = self._par.valores()["umbral_cuello_botella_pct"]
            for e in sim.estados:
                m, rho = sim.carga.get(e.codigo, (0.0, 0.0))
                lectura = ("no cabe en el turno ni sin esperas" if rho >= 100 else
                           "cuello de botella probable" if rho >= umbral else "holgura suficiente")
                rho_filas.append([f"{e.codigo} · {e.nombre}", e.capacidad, fmt(m, 0), fmt(rho, 1), lectura])
                rho_col.append(ROJO if rho >= 100 else NARANJA if rho >= umbral else None)
        self.vista.mostrar(resumen, filas, filas_reg, rho_filas, rho_col)
