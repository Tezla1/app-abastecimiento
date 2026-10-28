"""Reglas de validación integral del proyecto (PASS / WARNING / FAIL)."""
import math
from dataclasses import dataclass, field
from typing import Optional

from . import calculos
from .alertas import validar_rutas
from .analisis import distancias_ramas
from .entities import Taller
from .routing import red_conexa

PASS, WARNING, FAIL = "PASS", "WARNING", "FAIL"


@dataclass
class Hallazgo:
    estado: str
    codigo: str
    area: str
    mensaje: str
    corregir_en: str


@dataclass
class ContextoValidacion:
    taller: Taller
    estaciones: list = field(default_factory=list)
    conexiones: list = field(default_factory=list)
    tipos: list = field(default_factory=list)
    rutas: list = field(default_factory=list)
    pedidos: list = field(default_factory=list)
    robots: list = field(default_factory=list)
    escenarios: list = field(default_factory=list)
    registros: dict = field(default_factory=dict)  # escenario_id -> [Registro]
    holgura_robot_m: float = 0.0


def validar(ctx: ContextoValidacion) -> list[Hallazgo]:
    h: list[Hallazgo] = []

    def add(ok: bool, codigo: str, area: str, msg_ok: str, msg_mal: str, donde: str,
            gravedad: str = FAIL) -> None:
        h.append(Hallazgo(PASS if ok else gravedad, codigo, area, msg_ok if ok else msg_mal, donde))

    t = ctx.taller
    codigos = [e.codigo for e in ctx.estaciones]
    por_codigo = {e.codigo: e for e in ctx.estaciones}
    funciones = [e.funcion for e in ctx.estaciones]

    # --- Taller ---
    add(t.area_m2 > 0 and t.operadores > 0, "TAL-01", "Taller",
        "Datos básicos del taller completos.",
        "Área u operadores sin registrar (valen 0).", "Caracterización del taller", WARNING)

    # --- Layout ---
    add(len(ctx.estaciones) >= 2, "LAY-01", "Layout",
        f"{len(ctx.estaciones)} estaciones registradas.",
        "Se necesitan al menos 2 estaciones.", "Layout y movimientos")
    add(funciones.count("ALMACEN") == 1 and funciones.count("DESPACHO") == 1, "LAY-02", "Layout",
        "Hay exactamente un Almacén (inicio) y un Despacho (fin).",
        f"Se requiere 1 Almacén y 1 Despacho (hay {funciones.count('ALMACEN')} y {funciones.count('DESPACHO')}).",
        "Layout y movimientos")
    add(len(set(codigos)) == len(codigos), "LAY-03", "Layout",
        "Códigos de estación únicos.", "Hay códigos de estación repetidos.", "Layout y movimientos")
    huerfanas = [c for c in ctx.conexiones if c.origen not in por_codigo or c.destino not in por_codigo]
    add(not huerfanas, "LAY-04", "Layout",
        f"{len(ctx.conexiones)} conexiones válidas.",
        f"{len(huerfanas)} conexión(es) apuntan a estaciones inexistentes.", "Layout y movimientos")
    add(red_conexa(codigos, ctx.conexiones), "LAY-05", "Layout",
        "La red es conexa.", "La red tiene estaciones aisladas.", "Layout y movimientos")
    cortas = []
    for c in ctx.conexiones:
        a, b = por_codigo.get(c.origen), por_codigo.get(c.destino)
        if a and b and c.distancia_m < math.hypot(a.x - b.x, a.y - b.y) * 0.95:
            cortas.append(f"{c.origen}–{c.destino}")
    add(not cortas, "LAY-06", "Layout",
        "Distancias coherentes con las coordenadas.",
        "Distancia menor que la línea recta en: " + ", ".join(cortas) + ".",
        "Layout y movimientos", WARNING)
    sin_tiempo = [e.codigo for e in ctx.estaciones if e.funcion == "PROCESO" and e.tiempo_proceso_min <= 0]
    add(not sin_tiempo, "LAY-07", "Layout",
        "Todas las áreas de proceso tienen tiempo de proceso.",
        "Áreas de proceso sin tiempo (no generan cola ni demora): " + ", ".join(sin_tiempo) + ".",
        "Layout y movimientos", WARNING)

    # --- Prendas, rutas y pedidos ---
    add(len(ctx.tipos) >= 1, "PRO-01", "Procesos", f"{len(ctx.tipos)} tipo(s) de prenda.",
        "No hay tipos de prenda registrados.", "Layout y movimientos")
    errores_ruta = validar_rutas(ctx.rutas, ctx.estaciones)
    add(not errores_ruta, "PRO-02", "Procesos", f"{len(ctx.rutas)} ruta(s) de proceso válidas.",
        " ".join(errores_ruta), "Layout y movimientos")
    con_ruta = {r.tipo_prenda_id for r in ctx.rutas}
    nombres = {x.id: x.nombre for x in ctx.tipos}
    sin_ruta = sorted({nombres.get(p.tipo_prenda_id, "?") for p in ctx.pedidos if p.tipo_prenda_id not in con_ruta})
    add(not sin_ruta, "PRO-03", "Procesos", "Todas las prendas pedidas tienen ruta.",
        "Prendas pedidas sin ruta: " + ", ".join(sin_ruta) + ".", "Layout y movimientos")
    malas_frac = []
    for tp in ctx.tipos:
        total = sum(r.fraccion_pct for r in ctx.rutas if r.tipo_prenda_id == tp.id)
        if total and abs(total - 100) > 0.01:
            malas_frac.append(f"{tp.nombre} ({total:g} %)")
    add(not malas_frac, "PRO-04", "Procesos", "Las ramas de cada prenda suman 100 %.",
        "Fracciones que no suman 100 % (se normalizan): " + ", ".join(malas_frac) + ".",
        "Layout y movimientos", WARNING)
    if not errores_ruta:
        inalcanzables = [f"{r.prenda}/{r.ruta}" for r in distancias_ramas(
            ctx.estaciones, ctx.conexiones, ctx.tipos, ctx.rutas, 1.0) if not r.alcanzable]
        add(not inalcanzables, "PRO-05", "Procesos", "Todas las ramas son físicamente recorribles.",
            "Ramas sin camino entre sus estaciones: " + ", ".join(inalcanzables) + ".", "Layout y movimientos")
    add(len(ctx.pedidos) >= 1, "PED-01", "Pedidos", f"{len(ctx.pedidos)} pedidos registrados.",
        "No hay pedidos registrados.", "Layout y movimientos")
    sinteticos = sum(1 for p in ctx.pedidos if p.origen_datos == "SINTETICO")
    add(sinteticos == 0, "PED-02", "Pedidos", "Pedidos con datos reales.",
        f"{sinteticos} pedido(s) sintéticos: sirven para validar el software, no son evidencia empírica.",
        "Layout y movimientos", WARNING)

    # --- Robots ---
    ancho_red = min((c.ancho_m for c in ctx.conexiones), default=None)
    peso_max = max((x.peso_unidad_kg for x in ctx.tipos), default=0.0)
    for esc in ctx.escenarios:
        if esc.tipo != "AMR":
            continue
        robot = next((r for r in ctx.robots if r.id == esc.robot_id), None)
        if robot is None:
            h.append(Hallazgo(WARNING, "ROB-01", "Robot",
                              f"«{esc.nombre}» no tiene perfil de robot asociado (ancho no verificado).",
                              "Simulación"))
            continue
        req = robot.ancho_m + 2 * ctx.holgura_robot_m
        ok_ancho = ancho_red is None or req <= ancho_red
        add(ok_ancho, "ROB-02", "Robot",
            f"«{robot.nombre}» necesita {req:.2f} m libres y cabe en toda la red.",
            f"«{robot.nombre}» necesita {req:.2f} m libres (robot {robot.ancho_m:g} m + holguras) y hay "
            f"pasillos de {ancho_red:g} m: esos tramos quedan vetados.", "Diseño conceptual del robot", WARNING)
        add(robot.capacidad_kg >= peso_max, "ROB-03", "Robot",
            f"«{robot.nombre}» puede cargar al menos una unidad de cualquier prenda.",
            f"«{robot.nombre}» ({robot.capacidad_kg:g} kg) no carga una unidad de {peso_max:g} kg.",
            "Diseño conceptual del robot")

    # --- Escenarios y comparabilidad ---
    base = next((e for e in ctx.escenarios if e.tipo == "MANUAL"), None)
    alt = next((e for e in ctx.escenarios if e.tipo == "AMR"), None)
    add(base is not None and alt is not None, "ESC-01", "Escenarios",
        "Existen escenario base (S0) y alternativo (S1).",
        "Falta un escenario S0 · Manual y/o un S1 · AMR.", "Simulación")
    if base and alt:
        ind = {}
        for esc in (base, alt):
            regs = ctx.registros.get(esc.id, [])
            add(bool(regs), "ESC-02", "Escenarios",
                f"«{esc.nombre}» tiene {len(regs)} registros.",
                f"«{esc.nombre}» no tiene registros: ejecute la simulación.", "Simulación")
            ind[esc.id] = calculos.calcular_indicadores(esc.para_calculo(), [r.para_calculo() for r in regs])
        ok, problemas = calculos.verificar_comparable(ind[base.id], ind[alt.id])
        add(ok, "ESC-03", "Modelo matemático",
            "Los escenarios son comparables.", " ".join(problemas), "Simulación")
        n_b, n_a = len(ctx.registros.get(base.id, [])), len(ctx.registros.get(alt.id, []))
        add(n_b == n_a, "ESC-04", "Escenarios",
            "Ambos escenarios evalúan el mismo número de traslados.",
            f"S0 tiene {n_b} registros y S1 {n_a}: la comparación no es sobre los mismos traslados.",
            "Simulación", WARNING)
        add(base.factor_demanda_pct == alt.factor_demanda_pct, "ESC-05", "Escenarios",
            "Ambos escenarios usan la misma demanda.",
            f"Factor de demanda distinto (S0 {base.factor_demanda_pct:g} %, S1 {alt.factor_demanda_pct:g} %): "
            "no es un experimento controlado.", "Simulación", WARNING)
    return h
