import os
import shutil
import sqlite3

from ...version import ESQUEMA_BD

ESQUEMA = """
CREATE TABLE IF NOT EXISTS taller(
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, area_m2 REAL NOT NULL DEFAULT 0,
    operadores INTEGER NOT NULL DEFAULT 0, jornada_h REAL NOT NULL DEFAULT 8,
    origen_datos TEXT NOT NULL DEFAULT 'SINTETICO', observaciones TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS estacion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    codigo TEXT NOT NULL, nombre TEXT NOT NULL DEFAULT '', funcion TEXT NOT NULL,
    x REAL NOT NULL DEFAULT 0, y REAL NOT NULL DEFAULT 0,
    tiempo_proceso_min REAL NOT NULL DEFAULT 0, capacidad INTEGER NOT NULL DEFAULT 1,
    grupo TEXT NOT NULL DEFAULT '', UNIQUE(taller_id, codigo));
CREATE TABLE IF NOT EXISTS conexion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    origen TEXT NOT NULL, destino TEXT NOT NULL, distancia_m REAL NOT NULL,
    ancho_m REAL NOT NULL, bidireccional INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS tipo_prenda(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL, peso_unidad_kg REAL NOT NULL, unidades_por_lote INTEGER NOT NULL,
    factor_proceso REAL NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS ruta_proceso(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    tipo_prenda_id INTEGER NOT NULL REFERENCES tipo_prenda(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL, fraccion_pct REAL NOT NULL, secuencia TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pedido(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    tipo_prenda_id INTEGER NOT NULL REFERENCES tipo_prenda(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL, prioridad INTEGER NOT NULL DEFAULT 3,
    llegada_min REAL NOT NULL DEFAULT 0, vencimiento_min REAL NOT NULL DEFAULT 0,
    origen_datos TEXT NOT NULL DEFAULT 'SINTETICO');
CREATE TABLE IF NOT EXISTS robot(
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, capacidad_kg REAL NOT NULL,
    velocidad_ms REAL NOT NULL, ancho_m REAL NOT NULL, radio_giro_m REAL NOT NULL DEFAULT 0,
    origen_datos TEXT NOT NULL DEFAULT 'DISENO');
CREATE TABLE IF NOT EXISTS escenario(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL, tipo TEXT NOT NULL, num_recursos INTEGER NOT NULL,
    tiempo_observacion_min REAL NOT NULL, velocidad_ms REAL NOT NULL, capacidad_kg REAL NOT NULL,
    t_carga_s REAL NOT NULL DEFAULT 0, t_descarga_s REAL NOT NULL DEFAULT 0,
    nodo_inicial TEXT NOT NULL, reposicionamiento INTEGER NOT NULL DEFAULT 1,
    robot_id INTEGER REFERENCES robot(id) ON DELETE SET NULL,
    politica TEXT NOT NULL DEFAULT 'PRIORIDAD', balanceo INTEGER NOT NULL DEFAULT 1,
    factor_demanda_pct REAL NOT NULL DEFAULT 100, variabilidad_pct REAL NOT NULL DEFAULT 0,
    semilla INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS registro(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id INTEGER NOT NULL REFERENCES escenario(id) ON DELETE CASCADE,
    pedido_id INTEGER, lote INTEGER NOT NULL DEFAULT 0,
    desde TEXT NOT NULL DEFAULT '', hacia TEXT NOT NULL DEFAULT '', atendida INTEGER NOT NULL,
    tiempo_espera_min REAL NOT NULL DEFAULT 0, tiempo_recorrido_min REAL NOT NULL DEFAULT 0,
    distancia_m REAL NOT NULL DEFAULT 0, inicio_min REAL NOT NULL DEFAULT 0,
    fin_min REAL NOT NULL DEFAULT 0, recurso INTEGER NOT NULL DEFAULT 0,
    viajes INTEGER NOT NULL DEFAULT 1, detalle TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS cierre(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    codigo TEXT NOT NULL, motivo TEXT NOT NULL DEFAULT 'OTRO', detalle TEXT NOT NULL DEFAULT '',
    desde_min REAL NOT NULL DEFAULT 0, hasta_min REAL NOT NULL DEFAULT 0,
    bloquea_paso INTEGER NOT NULL DEFAULT 1, vigente INTEGER NOT NULL DEFAULT 1,
    registrado TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS stock(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    tipo_prenda_id INTEGER NOT NULL REFERENCES tipo_prenda(id) ON DELETE CASCADE,
    unidades INTEGER NOT NULL DEFAULT 0, stock_minimo INTEGER NOT NULL DEFAULT 0,
    UNIQUE(taller_id, tipo_prenda_id));
CREATE TABLE IF NOT EXISTS solicitud_compra(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taller_id INTEGER NOT NULL REFERENCES taller(id) ON DELETE CASCADE,
    tipo_prenda_id INTEGER NOT NULL REFERENCES tipo_prenda(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL, estado TEXT NOT NULL DEFAULT 'PENDIENTE',
    nota TEXT NOT NULL DEFAULT '', registrado TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS parametro(
    id INTEGER PRIMARY KEY AUTOINCREMENT, clave TEXT NOT NULL UNIQUE, valor REAL NOT NULL,
    unidad TEXT NOT NULL DEFAULT '', descripcion TEXT NOT NULL DEFAULT '',
    fuente TEXT NOT NULL DEFAULT '', verificado INTEGER NOT NULL DEFAULT 0);
"""

TABLAS = ("taller", "robot", "tipo_prenda", "estacion", "conexion", "ruta_proceso", "pedido",
          "escenario", "registro", "cierre", "stock", "solicitud_compra", "parametro")


def _es_esquema_antiguo(ruta: str) -> bool:
    try:
        c = sqlite3.connect(ruta)
        try:
            version = c.execute("PRAGMA user_version").fetchone()[0]
            hay_datos = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0] > 0
            # base vacía no cuenta como antigua
            return hay_datos and version < ESQUEMA_BD
        finally:
            c.close()
    except sqlite3.Error:
        return False


class Database:
    def __init__(self, ruta: str = ":memory:"):
        self.respaldo_v1: str = ""
        if ruta != ":memory:" and os.path.exists(ruta) and _es_esquema_antiguo(ruta):
            self.respaldo_v1 = ruta + ".v1.bak"
            n = 1
            while os.path.exists(self.respaldo_v1):
                n += 1
                self.respaldo_v1 = f"{ruta}.v1.{n}.bak"
            shutil.move(ruta, self.respaldo_v1)
        # check_same_thread=False: las operaciones largas corren en un hilo de trabajo (ver presentation/tareas.py);
        # mientras corren, un diálogo modal impide que la interfaz use la base al mismo tiempo
        self.conn = sqlite3.connect(ruta, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(ESQUEMA)
        self.conn.execute(f"PRAGMA user_version = {int(ESQUEMA_BD)}")
        self.conn.commit()
        self._marca = self.conn.total_changes

    def cambios_sin_guardar(self) -> int:
        """Filas modificadas desde la última marca (al abrir o al guardar un proyecto con nombre)."""
        return self.conn.total_changes - self._marca

    def marcar_guardado(self) -> None:
        self._marca = self.conn.total_changes

    def close(self) -> None:
        self.conn.close()
