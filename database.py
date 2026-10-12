import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "abastecimiento.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    area_m2 REAL CHECK (area_m2 IS NULL OR area_m2 >= 0),
    num_estaciones INTEGER CHECK (num_estaciones IS NULL OR num_estaciones >= 0),
    num_operarios INTEGER CHECK (num_operarios IS NULL OR num_operarios >= 0)
);

CREATE TABLE IF NOT EXISTS escenario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Base', 'Recurso móvil')),
    num_recursos INTEGER NOT NULL DEFAULT 1 CHECK (num_recursos >= 1),
    capacidad_kg REAL CHECK (capacidad_kg IS NULL OR capacidad_kg >= 0),
    velocidad_m_min REAL CHECK (velocidad_m_min IS NULL OR velocidad_m_min >= 0),
    obstaculos INTEGER NOT NULL DEFAULT 0 CHECK (obstaculos IN (0, 1)),
    tiempo_observacion_min REAL CHECK (tiempo_observacion_min IS NULL OR tiempo_observacion_min > 0),
    UNIQUE (empresa_id, nombre)
);

CREATE TABLE IF NOT EXISTS registro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id INTEGER NOT NULL REFERENCES escenario(id) ON DELETE CASCADE,
    origen TEXT NOT NULL,
    destino TEXT NOT NULL,
    distancia_m REAL NOT NULL CHECK (distancia_m >= 0),
    carga_kg REAL NOT NULL CHECK (carga_kg >= 0),
    tiempo_espera_min REAL NOT NULL CHECK (tiempo_espera_min >= 0),
    tiempo_recorrido_min REAL NOT NULL CHECK (tiempo_recorrido_min >= 0),
    atendida INTEGER NOT NULL CHECK (atendida IN (0, 1))
);
"""


def conectar():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite lo trae apagado por defecto
    return conn


def inicializar():
    conn = conectar()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _ejecutar(sql, params=()):
    conn = conectar()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _consultar(sql, params=()):
    conn = conectar()
    try:
        return [dict(fila) for fila in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


# ---------- Empresa ----------
def crear_empresa(nombre, area_m2=None, num_estaciones=None, num_operarios=None):
    return _ejecutar(
        "INSERT INTO empresa (nombre, area_m2, num_estaciones, num_operarios) "
        "VALUES (?, ?, ?, ?)",
        (nombre, area_m2, num_estaciones, num_operarios),
    )


def listar_empresas():
    return _consultar("SELECT * FROM empresa ORDER BY nombre")


def eliminar_empresa(empresa_id):
    _ejecutar("DELETE FROM empresa WHERE id = ?", (empresa_id,))


# ---------- Escenario ----------
def crear_escenario(empresa_id, nombre, tipo, num_recursos=1, capacidad_kg=None,
                    velocidad_m_min=None, obstaculos=False, tiempo_observacion_min=None):
    return _ejecutar(
        "INSERT INTO escenario (empresa_id, nombre, tipo, num_recursos, capacidad_kg, "
        "velocidad_m_min, obstaculos, tiempo_observacion_min) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (empresa_id, nombre, tipo, num_recursos, capacidad_kg,
         velocidad_m_min, int(obstaculos), tiempo_observacion_min),
    )


def listar_escenarios(empresa_id):
    return _consultar("SELECT * FROM escenario WHERE empresa_id = ? ORDER BY id", (empresa_id,))


def eliminar_escenario(escenario_id):
    _ejecutar("DELETE FROM escenario WHERE id = ?", (escenario_id,))


# ---------- Registro experimental ----------
def crear_registro(escenario_id, origen, destino, distancia_m, carga_kg,
                   tiempo_espera_min, tiempo_recorrido_min, atendida):
    return _ejecutar(
        "INSERT INTO registro (escenario_id, origen, destino, distancia_m, carga_kg, "
        "tiempo_espera_min, tiempo_recorrido_min, atendida) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (escenario_id, origen, destino, distancia_m, carga_kg,
         tiempo_espera_min, tiempo_recorrido_min, int(atendida)),
    )


def listar_registros(escenario_id):
    return _consultar("SELECT * FROM registro WHERE escenario_id = ? ORDER BY id", (escenario_id,))


def eliminar_registro(registro_id):
    _ejecutar("DELETE FROM registro WHERE id = ?", (registro_id,))

def contar_registros_empresa(empresa_id):
    """Total de registros de todos los escenarios de una empresa."""
    filas = _consultar(
        "SELECT COUNT(*) AS n FROM registro r "
        "JOIN escenario e ON e.id = r.escenario_id WHERE e.empresa_id = ?",
        (empresa_id,),
    )
    return filas[0]["n"]