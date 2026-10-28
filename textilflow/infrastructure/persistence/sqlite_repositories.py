import sqlite3
from dataclasses import fields
from typing import Generic, Optional, TypeVar

from ...application import ports
from ...domain.entities import (Cierre, Conexion, Escenario, Estacion, Parametro, Pedido, Registro,
                                Robot, RutaProceso, Taller, TipoPrenda)
from .database import TABLAS, Database

T = TypeVar("T")


class _SqliteRepo(Generic[T]):
    tabla: str
    entidad: type

    def __init__(self, db: Database):
        self._db = db
        self._cols = [f.name for f in fields(self.entidad) if f.name != "id"]
        self._bools = {f.name for f in fields(self.entidad) if f.type is bool}

    def _a_entidad(self, fila: sqlite3.Row) -> T:
        datos = {c: fila[c] for c in self._cols}
        for b in self._bools:
            datos[b] = bool(datos[b])
        return self.entidad(id=fila["id"], **datos)

    def _valores(self, e: T) -> list:
        return [getattr(e, c) for c in self._cols]

    def add(self, e: T) -> T:
        cols = ", ".join(self._cols)
        marcas = ", ".join("?" for _ in self._cols)
        with self._db.conn:
            cur = self._db.conn.execute(f"INSERT INTO {self.tabla}({cols}) VALUES({marcas})", self._valores(e))
        e.id = cur.lastrowid
        return e

    def update(self, e: T) -> T:
        sets = ", ".join(f"{c} = ?" for c in self._cols)
        with self._db.conn:
            self._db.conn.execute(f"UPDATE {self.tabla} SET {sets} WHERE id = ?", self._valores(e) + [e.id])
        return e

    def get(self, id: int) -> Optional[T]:
        fila = self._db.conn.execute(f"SELECT * FROM {self.tabla} WHERE id = ?", (id,)).fetchone()
        return self._a_entidad(fila) if fila else None

    def delete(self, id: int) -> None:
        with self._db.conn:
            self._db.conn.execute(f"DELETE FROM {self.tabla} WHERE id = ?", (id,))

    def list_all(self) -> list[T]:
        filas = self._db.conn.execute(f"SELECT * FROM {self.tabla} ORDER BY id").fetchall()
        return [self._a_entidad(f) for f in filas]

    def _list_where(self, columna: str, valor) -> list[T]:
        assert columna in self._cols
        filas = self._db.conn.execute(
            f"SELECT * FROM {self.tabla} WHERE {columna} = ? ORDER BY id", (valor,)).fetchall()
        return [self._a_entidad(f) for f in filas]


class SqliteTallerRepository(_SqliteRepo[Taller], ports.TallerRepository):
    tabla, entidad = "taller", Taller


class SqliteRobotRepository(_SqliteRepo[Robot], ports.RobotRepository):
    tabla, entidad = "robot", Robot


class SqliteEstacionRepository(_SqliteRepo[Estacion], ports.EstacionRepository):
    tabla, entidad = "estacion", Estacion

    def list_by_taller(self, taller_id: int) -> list[Estacion]:
        return self._list_where("taller_id", taller_id)


class SqliteConexionRepository(_SqliteRepo[Conexion], ports.ConexionRepository):
    tabla, entidad = "conexion", Conexion

    def list_by_taller(self, taller_id: int) -> list[Conexion]:
        return self._list_where("taller_id", taller_id)


class SqliteCierreRepository(_SqliteRepo[Cierre], ports.CierreRepository):
    tabla, entidad = "cierre", Cierre

    def list_by_taller(self, taller_id: int) -> list[Cierre]:
        return self._list_where("taller_id", taller_id)


class SqliteTipoPrendaRepository(_SqliteRepo[TipoPrenda], ports.TipoPrendaRepository):
    tabla, entidad = "tipo_prenda", TipoPrenda


class SqliteRutaProcesoRepository(_SqliteRepo[RutaProceso], ports.RutaProcesoRepository):
    tabla, entidad = "ruta_proceso", RutaProceso

    def list_by_taller(self, taller_id: int) -> list[RutaProceso]:
        return self._list_where("taller_id", taller_id)


class SqlitePedidoRepository(_SqliteRepo[Pedido], ports.PedidoRepository):
    tabla, entidad = "pedido", Pedido

    def list_by_taller(self, taller_id: int) -> list[Pedido]:
        return self._list_where("taller_id", taller_id)


class SqliteParametroRepository(_SqliteRepo[Parametro], ports.ParametroRepository):
    tabla, entidad = "parametro", Parametro


class SqliteEscenarioRepository(_SqliteRepo[Escenario], ports.EscenarioRepository):
    tabla, entidad = "escenario", Escenario

    def list_by_taller(self, taller_id: int) -> list[Escenario]:
        return self._list_where("taller_id", taller_id)


class SqliteRegistroRepository(_SqliteRepo[Registro], ports.RegistroRepository):
    tabla, entidad = "registro", Registro

    def list_by_escenario(self, escenario_id: int) -> list[Registro]:
        return self._list_where("escenario_id", escenario_id)

    def replace_for_escenario(self, escenario_id: int, registros: list[Registro]) -> None:
        cols = ", ".join(self._cols)
        marcas = ", ".join("?" for _ in self._cols)
        with self._db.conn:
            self._db.conn.execute("DELETE FROM registro WHERE escenario_id = ?", (escenario_id,))
            self._db.conn.executemany(
                f"INSERT INTO registro({cols}) VALUES({marcas})", [self._valores(r) for r in registros])


class SqliteSnapshotRepository(ports.SnapshotRepository):
    def __init__(self, db: Database):
        self._db = db

    def dump(self) -> dict:
        return {t: [dict(f) for f in self._db.conn.execute(f"SELECT * FROM {t} ORDER BY id")]
                for t in TABLAS}

    def load(self, datos: dict) -> None:
        conn = self._db.conn
        columnas = {t: [r["name"] for r in conn.execute(f"PRAGMA table_info({t})")] for t in TABLAS}
        for t in TABLAS:
            filas = datos.get(t, [])
            if not isinstance(filas, list):
                raise ValueError(f"Tabla «{t}» con formato inválido.")
            for fila in filas:
                if not isinstance(fila, dict) or "id" not in fila:
                    raise ValueError(f"Fila inválida en la tabla «{t}».")
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            with conn:
                for t in reversed(TABLAS):
                    conn.execute(f"DELETE FROM {t}")
                for t in TABLAS:
                    for fila in datos.get(t, []):
                        cols = [c for c in columnas[t] if c in fila]
                        conn.execute(
                            f"INSERT INTO {t}({', '.join(cols)}) VALUES({', '.join('?' for _ in cols)})",
                            [fila[c] for c in cols])
                problemas = conn.execute("PRAGMA foreign_key_check").fetchall()
                if problemas:
                    raise ValueError("El respaldo tiene referencias rotas entre tablas.")
        except sqlite3.Error as e:
            raise ValueError(f"datos incompatibles con el esquema ({e})") from None
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
