# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Página del Data Manager: tarjetas para importar, exportar, respaldar y cargar el ejemplo.

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPlainTextEdit,
                             QPushButton, QVBoxLayout)

from .. import theme
from ..widgets.common import VistaPagina
from ..widgets.adaptable import FilaAdaptable


def _tarjeta(titulo: str, detalle: str, boton: str, estilo: str = "") -> tuple:
    f = QFrame()
    f.setObjectName("tarjeta")
    lay = QVBoxLayout(f)
    t = QLabel(titulo)
    t.setStyleSheet("font-weight: 700; font-size: 13px;")
    d = QLabel(detalle)
    d.setObjectName("tenue")
    d.setWordWrap(True)
    b = QPushButton(boton)
    if estilo:
        b.setObjectName(estilo)
    lay.addWidget(t)
    lay.addWidget(d, 1)
    lay.addWidget(b)
    return f, b


class DataManagerView(VistaPagina):
    plantilla_solicitada = pyqtSignal(str)
    importar_solicitado = pyqtSignal(str)
    exportar_solicitado = pyqtSignal(str)
    exportar_proyecto_solicitado = pyqtSignal(str)
    restaurar_solicitado = pyqtSignal(str)
    demo_solicitado = pyqtSignal()
    ejemplo_archivo_solicitado = pyqtSignal(str)
    respaldos_solicitados = pyqtSignal()

    def __init__(self):
        super().__init__("Data Manager",
                         "Importación masiva, exportación, respaldo y transferencia de proyectos.", theme.TURQUESA)
        t = QLabel("Excel empresarial")
        t.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(t)
        fila = FilaAdaptable()
        c1, b1 = _tarjeta("01 · Crear plantilla Excel", "Genera un libro con las hojas Taller, Nodos, Conexiones y Ordenes_Logisticas.", "Crear plantilla…")
        c2, b2 = _tarjeta("02 · Validar e importar Excel", "Verifica estructura y datos; si hay errores no se importa nada.", "Importar…", "primario")
        c3, b3 = _tarjeta("03 · Exportar datos del taller", "Exporta nodos, conexiones y órdenes del taller activo.", "Exportar…")
        for c in (c1, c2, c3):
            fila.addWidget(c)
        self.cuerpo.addLayout(fila)

        t2 = QLabel("Proyecto restaurable (.rlr)")
        t2.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(t2)
        fila2 = FilaAdaptable()
        c4, b4 = _tarjeta("Exportar proyecto (.rlr)", "Respaldo completo: talleres, layout, prendas, rutas, pedidos, robots, escenarios, registros y parámetros.", "Exportar…")
        c5, b5 = _tarjeta("Restaurar proyecto (.rlr)", "REEMPLAZA todos los datos actuales por los del respaldo.", "Restaurar…", "peligro")
        c7, b7 = _tarjeta("Cargar ejemplo desde archivo",
                          "Elija un ejemplo .xlsx (carpeta «ejemplos» o uno generado por una IA con el formato de la plantilla). "
                          "No borra nada: crea un taller nuevo con su escenario S0 listo para simular.", "Elegir archivo…", "primario")
        for c in (c4, c5, c7):
            fila2.addWidget(c)
        self.cuerpo.addLayout(fila2)

        t2b = QLabel("Ejemplo integrado")
        t2b.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(t2b)
        fila3 = FilaAdaptable()
        c6, b6 = _tarjeta("Datos de ejemplo", "Carga el caso experimental sintético: 9 áreas, 4 prendas, 8 ramas, 5 pedidos, S0 vs S1.", "Cargar ejemplo")
        fila3.addWidget(c6)
        c8, b8 = _tarjeta("Respaldos automáticos (últimos 3)",
                          "TextilFlow guarda solo un respaldo cada 5 minutos si hubo cambios, y al cerrar. "
                          "Aquí puede volver a cualquiera de los 3 más recientes.", "Ver y restaurar…")
        fila3.addWidget(c8)
        fila3.addStretch(1)
        self.cuerpo.addLayout(fila3)

        t3 = QLabel("Información")
        t3.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.cuerpo.addWidget(t3)
        self.info_texto = QPlainTextEdit()
        self.info_texto.setReadOnly(True)
        self.info_texto.setPlaceholderText("Aquí aparecerá la validación de archivos y operaciones realizadas.")
        self.cuerpo.addWidget(self.info_texto, 1)

        b1.clicked.connect(lambda: self._guardar("Crear plantilla", "plantilla_TextilFlow.xlsx", "Excel (*.xlsx)", self.plantilla_solicitada))
        b2.clicked.connect(lambda: self._abrir("Importar Excel", "Excel (*.xlsx)", self.importar_solicitado))
        b3.clicked.connect(lambda: self._guardar("Exportar taller", "taller.xlsx", "Excel (*.xlsx)", self.exportar_solicitado))
        b4.clicked.connect(lambda: self._guardar("Exportar proyecto", "proyecto.rlr", "Proyecto TextilFlow (*.rlr)", self.exportar_proyecto_solicitado))
        b5.clicked.connect(self._restaurar)
        b6.clicked.connect(self.demo_solicitado.emit)
        b7.clicked.connect(self._ejemplo_archivo)
        b8.clicked.connect(self.respaldos_solicitados.emit)

    def info(self, mensaje: str) -> None:
        self.info_texto.appendPlainText(mensaje)

    def _guardar(self, titulo, nombre, filtro, senal) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, titulo, nombre, filtro)
        if ruta:
            ext = filtro[filtro.index("*") + 1:-1]
            senal.emit(ruta if ruta.lower().endswith(ext) else ruta + ext)

    def _abrir(self, titulo, filtro, senal) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, titulo, "", filtro)
        if ruta:
            senal.emit(ruta)

    def _ejemplo_archivo(self) -> None:
        carpeta = Path(__file__).resolve().parents[3] / "ejemplos"
        ruta, _ = QFileDialog.getOpenFileName(self, "Cargar ejemplo desde archivo",
                                              str(carpeta if carpeta.is_dir() else Path.home()), "Ejemplo Excel (*.xlsx)")
        if ruta:
            self.ejemplo_archivo_solicitado.emit(ruta)

    def elegir_respaldo(self, etiquetas: list) -> int:
        from PyQt6.QtWidgets import QInputDialog
        texto, ok = QInputDialog.getItem(self, "Respaldos automáticos", "Elija el respaldo a restaurar:", etiquetas, 0, False)
        return etiquetas.index(texto) if ok and texto in etiquetas else -1

    def _restaurar(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Restaurar proyecto", "", "Proyecto TextilFlow (*.rlr)")
        if ruta and self.confirmar("Esto reemplazará TODOS los datos actuales. ¿Continuar?"):
            self.restaurar_solicitado.emit(ruta)
