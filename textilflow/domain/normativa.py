"""Parámetros normativos / de diseño y verificación de cumplimiento.

IMPORTANTE: cada parámetro indica su fuente y si fue contrastado con el texto de la norma
(`verificado`). Los valores marcados como NO verificados son criterios de diseño o citas
secundarias: el estudio debe confirmarlos antes de usarlos como argumento legal.
"""
import math
from dataclasses import dataclass
from typing import Iterable

from .entities import Conexion, Escenario, Estacion, Parametro, Robot, Taller

CUMPLE, ADVERTENCIA, INCUMPLE = "CUMPLE", "ADVERTENCIA", "INCUMPLE"

PARAMETROS_DEFECTO = [
    Parametro("ancho_min_pasillo_m", 1.20, "m",
              "Ancho mínimo de los pasillos interiores de los locales de trabajo",
              "Res. 2400/1979, Art. 12", True),
    Parametro("dist_min_entre_maquinas_m", 0.80, "m",
              "Distancia mínima entre máquinas, aparatos o equipos",
              "Res. 2400/1979, Art. 12 par. 1", True),
    Parametro("area_min_por_trabajador_m2", 2.0, "m²",
              "Superficie de pavimento mínima por trabajador",
              "Res. 2400/1979, Art. 9", True),
    Parametro("vel_max_sin_deteccion_ms", 0.30, "m/s",
              "Velocidad máxima de un vehículo sin conductor si la detección de personas está inhibida",
              "ISO 3691-4 (resumen secundario de TÜV/Fabrico; confirmar en la norma)", False),
    Parametro("holgura_lateral_robot_m", 0.25, "m",
              "Holgura libre a cada lado del robot para considerar un pasillo transitable",
              "Criterio de diseño del estudio (ISO 3691-4 lo deja a la evaluación de riesgos)", False),
    Parametro("vel_max_zona_compartida_ms", 1.00, "m/s",
              "Velocidad máxima de diseño del AMR en pasillos compartidos con personas",
              "Criterio de diseño del estudio (definir en la evaluación de riesgos)", False),
    Parametro("carga_manual_max_hombres_kg", 25.0, "kg",
              "Carga máxima recomendada por persona en levantamiento manual (hombres)",
              "Res. 2400/1979 y Res. 1409/2012 según cita secundaria; confirmar en el texto oficial", False),
    Parametro("carga_manual_max_mujeres_kg", 12.5, "kg",
              "Carga máxima recomendada por persona en levantamiento manual (mujeres)",
              "Res. 2400/1979 según cita secundaria (12–12,5 kg); confirmar en el texto oficial", False),
    Parametro("utilizacion_objetivo_flota_pct", 75.0, "%",
              "Utilización objetivo de la flota al dimensionarla (deja margen a picos y averías)",
              "Criterio de diseño del estudio", False),
    Parametro("umbral_cuello_botella_pct", 85.0, "%",
              "Utilización de una estación a partir de la cual se considera cuello de botella",
              "Criterio de diseño del estudio", False),
    Parametro("umbral_espera_cola_min", 30.0, "min",
              "Espera media en cola de una estación que dispara una alerta",
              "Criterio de diseño del estudio", False),
    Parametro("umbral_saturacion_flota_pct", 90.0, "%",
              "Utilización de la flota que se considera saturada",
              "Criterio de diseño del estudio", False),
    Parametro("umbral_flota_ociosa_pct", 15.0, "%",
              "Utilización de la flota por debajo de la cual se considera sobredimensionada",
              "Criterio de diseño del estudio", False),
]


def valores(parametros: Iterable[Parametro]) -> dict:
    """{clave: valor}; completa con los valores por defecto si falta alguno."""
    out = {p.clave: p.valor for p in PARAMETROS_DEFECTO}
    out.update({p.clave: p.valor for p in parametros})
    return out


@dataclass
class Cumplimiento:
    estado: str
    clave: str
    regla: str
    detalle: str
    fuente: str
    verificado: bool


def ancho_requerido_robot(robot: Robot, par: dict) -> float:
    """Ancho libre que necesita un robot: su ancho + holgura a cada lado."""
    return robot.ancho_m + 2 * par["holgura_lateral_robot_m"]


def evaluar(par: dict, taller: Taller, estaciones: list[Estacion], conexiones: list[Conexion],
            escenarios: list[Escenario], robots: list[Robot]) -> list[Cumplimiento]:
    fuentes = {p.clave: (p.fuente, p.verificado) for p in PARAMETROS_DEFECTO}
    out: list[Cumplimiento] = []

    def add(estado: str, clave: str, regla: str, detalle: str) -> None:
        f, v = fuentes[clave]
        out.append(Cumplimiento(estado, clave, regla, detalle, f, v))

    # Pasillos
    minimo = par["ancho_min_pasillo_m"]
    angostos = [f"{c.origen}–{c.destino} ({c.ancho_m:g} m)" for c in conexiones if c.ancho_m < minimo]
    add(INCUMPLE if angostos else CUMPLE, "ancho_min_pasillo_m", f"Pasillos ≥ {minimo:g} m",
        ("Por debajo del mínimo: " + ", ".join(angostos)) if angostos
        else f"Los {len(conexiones)} pasillos cumplen el mínimo.")

    # Distancia entre máquinas (aproximada con las coordenadas de las áreas de proceso)
    proc = [e for e in estaciones if e.funcion == "PROCESO"]
    cerca = [f"{a.codigo}–{b.codigo}" for i, a in enumerate(proc) for b in proc[i + 1:]
             if math.hypot(a.x - b.x, a.y - b.y) < par["dist_min_entre_maquinas_m"]]
    add(ADVERTENCIA if cerca else CUMPLE, "dist_min_entre_maquinas_m",
        f"Distancia entre equipos ≥ {par['dist_min_entre_maquinas_m']:g} m",
        ("Áreas demasiado juntas: " + ", ".join(cerca)) if cerca else "Las áreas de proceso están separadas.")

    # Área por trabajador
    if taller.area_m2 > 0 and taller.operadores > 0:
        por_op = taller.area_m2 / taller.operadores
        ok = por_op >= par["area_min_por_trabajador_m2"]
        add(CUMPLE if ok else INCUMPLE, "area_min_por_trabajador_m2",
            f"Área por trabajador ≥ {par['area_min_por_trabajador_m2']:g} m²",
            f"{por_op:.1f} m² por trabajador ({taller.area_m2:g} m² / {taller.operadores}).")
    else:
        add(ADVERTENCIA, "area_min_por_trabajador_m2", "Área por trabajador",
            "Registre el área y los operadores del taller para verificar.")

    for esc in escenarios:
        if esc.tipo == "AMR":
            robot = next((r for r in robots if r.id == esc.robot_id), None)
            if robot:
                req = ancho_requerido_robot(robot, par)
                vetados = [f"{c.origen}–{c.destino} ({c.ancho_m:g} m)" for c in conexiones if c.ancho_m < req]
                add(ADVERTENCIA if vetados else CUMPLE, "holgura_lateral_robot_m",
                    f"«{esc.nombre}»: pasillo ≥ ancho del robot + 2 × holgura = {req:.2f} m",
                    ("Pasillos vetados para el AMR: " + ", ".join(vetados)) if vetados
                    else "El AMR puede circular por todos los pasillos.")
            lim = par["vel_max_zona_compartida_ms"]
            add(ADVERTENCIA if esc.velocidad_ms > lim else CUMPLE, "vel_max_zona_compartida_ms",
                f"«{esc.nombre}»: velocidad ≤ {lim:g} m/s en zonas compartidas",
                f"Velocidad del escenario: {esc.velocidad_ms:g} m/s. "
                f"Con detección de personas inhibida el límite sería {par['vel_max_sin_deteccion_ms']:g} m/s.")
        else:
            lim_h, lim_m = par["carga_manual_max_hombres_kg"], par["carga_manual_max_mujeres_kg"]
            if esc.capacidad_kg > lim_h:
                add(ADVERTENCIA, "carga_manual_max_hombres_kg", f"«{esc.nombre}»: carga por persona ≤ {lim_h:g} kg",
                    f"El escenario asume {esc.capacidad_kg:g} kg por viaje: solo es aceptable con carro o ayuda mecánica.")
            elif esc.capacidad_kg > lim_m:
                add(ADVERTENCIA, "carga_manual_max_mujeres_kg",
                    f"«{esc.nombre}»: carga por persona ≤ {lim_m:g} kg para mujeres",
                    f"{esc.capacidad_kg:g} kg por viaje supera el límite para mujeres; asigne el traslado con criterio.")
            else:
                add(CUMPLE, "carga_manual_max_hombres_kg", f"«{esc.nombre}»: carga manual por viaje",
                    f"{esc.capacidad_kg:g} kg por viaje, dentro de los límites de levantamiento.")
    return out
