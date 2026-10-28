from datetime import datetime

from ...domain.entities import Taller
from ...version import FORMATO_RLR
from ..errors import ErrorDeNegocio
from ..ports import ExcelGateway, ProyectoArchive, SnapshotRepository
from .layout import GestionarLayout
from .procesos import GestionarProcesos
from .talleres import GestionarTalleres

VERSION_FORMATO = FORMATO_RLR


class GestionarDatos:
    def __init__(self, talleres: GestionarTalleres, layout: GestionarLayout, procesos: GestionarProcesos,
                 excel: ExcelGateway, snapshot: SnapshotRepository, archivo: ProyectoArchive):
        self._talleres = talleres
        self._layout = layout
        self._procesos = procesos
        self._excel = excel
        self._snapshot = snapshot
        self._archivo = archivo

    def crear_plantilla(self, ruta: str) -> None:
        self._excel.crear_plantilla(ruta)

    def exportar_taller(self, taller_id: int, ruta: str) -> None:
        taller = self._talleres.obtener(taller_id)
        if taller is None:
            raise ErrorDeNegocio("Seleccione un taller para exportar.")
        self._excel.escribir_taller(
            ruta, taller,
            self._layout.listar_estaciones(taller_id),
            self._layout.listar_conexiones(taller_id),
            self._procesos.listar_tipos(),
            self._procesos.listar_rutas(taller_id),
            self._procesos.listar_pedidos(taller_id),
        )

    def importar_taller(self, ruta: str) -> tuple[Taller, str]:
        datos = self._excel.leer_taller(ruta)
        errores = list(datos.errores)
        if datos.taller is None and not errores:
            errores.append("La hoja «Taller» no tiene datos.")
        if not errores:
            errores += [f"Taller: {m}" for m in datos.taller.validar()]
            codigos = set()
            for i, e in enumerate(datos.estaciones, 2):
                errores += [f"Nodos fila {i}: {m}" for m in e.validar()]
                if e.codigo in codigos:
                    errores.append(f"Nodos fila {i}: código «{e.codigo}» repetido.")
                codigos.add(e.codigo)
            for i, c in enumerate(datos.conexiones, 2):
                errores += [f"Conexiones fila {i}: {m}" for m in c.validar()]
                for cod in (c.origen, c.destino):
                    if cod not in codigos:
                        errores.append(f"Conexiones fila {i}: la estación «{cod}» no está en la hoja Nodos.")
            nombres = set()
            for i, t in enumerate(datos.tipos, 2):
                errores += [f"Prendas fila {i}: {m}" for m in t.validar()]
                if t.nombre.lower() in nombres:
                    errores.append(f"Prendas fila {i}: «{t.nombre}» repetida.")
                nombres.add(t.nombre.lower())
            for i, (prenda, r) in enumerate(datos.rutas, 2):
                errores += [f"Rutas fila {i}: {m}" for m in r.validar()]
                if prenda.lower() not in nombres:
                    errores.append(f"Rutas fila {i}: la prenda «{prenda}» no está en la hoja Prendas.")
                for paso in r.pasos():
                    if paso.startswith("@"):
                        if not any(e.grupo == paso[1:] for e in datos.estaciones):
                            errores.append(f"Rutas fila {i}: el grupo «{paso}» no existe en Nodos.")
                    elif paso not in codigos:
                        errores.append(f"Rutas fila {i}: el paso «{paso}» no está en la hoja Nodos.")
            for i, (prenda, p) in enumerate(datos.pedidos, 2):
                errores += [f"Pedidos fila {i}: {m}" for m in p.validar()]
                if prenda.lower() not in nombres:
                    errores.append(f"Pedidos fila {i}: la prenda «{prenda}» no está en la hoja Prendas.")
        if errores:
            resumen = "\n".join(errores[:15]) + (f"\n… y {len(errores) - 15} error(es) más." if len(errores) > 15 else "")
            raise ErrorDeNegocio("El archivo tiene errores y no se importó nada:\n" + resumen)

        taller = self._talleres.guardar(datos.taller)
        try:
            for e in datos.estaciones:
                e.taller_id = taller.id
                self._layout.guardar_estacion(e)
            for c in datos.conexiones:
                c.taller_id = taller.id
                self._layout.guardar_conexion(c)
            ids = {}
            for t in datos.tipos:
                existente = next((x for x in self._procesos.listar_tipos() if x.nombre.lower() == t.nombre.lower()), None)
                if existente:
                    ids[t.nombre.lower()] = existente.id
                else:
                    ids[t.nombre.lower()] = self._procesos.guardar_tipo(t).id
            for prenda, r in datos.rutas:
                r.taller_id, r.tipo_prenda_id = taller.id, ids[prenda.lower()]
                self._procesos.guardar_ruta(r)
            for prenda, p in datos.pedidos:
                p.taller_id, p.tipo_prenda_id = taller.id, ids[prenda.lower()]
                self._procesos.guardar_pedido(p)
        except ErrorDeNegocio:
            self._talleres.eliminar(taller.id)
            raise
        resumen = (f"Importado «{taller.nombre}»: {len(datos.estaciones)} nodos, "
                   f"{len(datos.conexiones)} conexiones, {len(datos.rutas)} ramas, {len(datos.pedidos)} pedidos.")
        return taller, resumen

    def exportar_proyecto(self, ruta: str) -> None:
        self._archivo.escribir(ruta, {
            "formato": "TEXTILFLOW-RLR",
            "version": VERSION_FORMATO,
            "creado": datetime.now().isoformat(timespec="seconds"),
            "tablas": self._snapshot.dump(),
        })

    def restaurar_proyecto(self, ruta: str) -> None:
        datos = self._archivo.leer(ruta)
        formatos_validos = ("TEXTILFLOW-RLR", "INTRABOT-RLR")
        if datos.get("formato") not in formatos_validos or "tablas" not in datos:
            raise ErrorDeNegocio("El archivo no es un respaldo de proyecto TextilFlow válido.")
        if datos.get("version") != VERSION_FORMATO:
            raise ErrorDeNegocio(f"Versión de respaldo no soportada: {datos.get('version')}.")
        try:
            self._snapshot.load(datos["tablas"])
        except ValueError as e:
            raise ErrorDeNegocio(f"Respaldo inválido: {e}. No se modificó ningún dato.") from None
