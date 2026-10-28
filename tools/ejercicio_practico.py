"""Ejercicio práctico de TextilFlow: N pruebas sobre el caso experimental sintético.

Uso:  python tools/ejercicio_practico.py [--replicas 30] [--salida docs]

Genera `EJERCICIO_PRACTICO.md`, `ejercicio_resultados.csv` y gráficos PNG (si hay matplotlib).
Todo es reproducible: las semillas son fijas.
"""
import argparse
import csv
import os
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from textilflow.container import construir                      # noqa: E402
from textilflow.domain import estadistica                       # noqa: E402
from textilflow.version import FECHA, VERSION                   # noqa: E402


def f(x, d=1):
    return "—" if x is None else f"{x:.{d}f}"


def ic(r, d=1):
    if r.media is None:
        return "—"
    if r.ic_inf is None:
        return f"{r.media:.{d}f}"
    return f"{r.media:.{d}f} ± {(r.ic_sup - r.ic_inf) / 2:.{d}f}"


class Ejercicio:
    def __init__(self, n: int):
        self.n = n
        self.app = construir(":memory:")
        self.taller = self.app.demo.execute()
        self.s0, self.s1 = self.app.escenarios.listar(self.taller.id)
        self.md: list[str] = []
        self.csv: list[dict] = []
        self.figuras: dict = {}

    # ---- utilidades
    def correr(self, esc, **cambios):
        e = replace(esc, **cambios)
        self.app.escenarios.guardar(e)
        try:
            return self.app.simulacion.execute(e.id, guardar=False)
        finally:
            self.app.escenarios.guardar(esc)      # restaura el escenario original

    def replicas(self, esc, n=None, **cambios):
        vals = {"makespan": [], "lead": [], "lead1": [], "ok": [], "tiempo": [], "tarde1": []}
        for i in range(n or self.n):
            r = self.correr(esc, semilla=100 + i, **cambios)
            vals["makespan"].append(r.ind.makespan_min)
            vals["lead"].append(r.ind.lead_time_prom_min)
            vals["lead1"].append(r.ind.lead_time_por_prioridad.get(1))
            vals["ok"].append(r.ind.completados_pct)
            vals["tiempo"].append(r.ind.pedidos_a_tiempo_pct)
        return {k: estadistica.resumir(v) for k, v in vals.items()}, vals

    def h(self, texto):
        self.md += ["", texto, ""]

    def tabla(self, cab, filas):
        self.md.append("| " + " | ".join(cab) + " |")
        self.md.append("|" + "|".join("---" for _ in cab) + "|")
        for fila in filas:
            self.md.append("| " + " | ".join(str(c) for c in fila) + " |")
        self.md.append("")

    # ---- pruebas
    def p1_base(self):
        self.h("## Prueba 1 · Un turno base (S0 manual vs S1 AMR)")
        filas = []
        for e in (self.s0, self.s1):
            r = self.app.simulacion.execute(e.id, guardar=False)
            filas.append([e.nombre, f"{r.ind.lotes_completados}/{r.ind.lotes}", f(r.ind.makespan_min, 0), f(r.ind.lead_time_prom_min, 0),
                          f(r.ind.pedidos_a_tiempo_pct, 0) + " %", f(r.indicadores["espera_prom"], 2),
                          f(r.indicadores["utilizacion_pct"], 1) + " %", len(r.alertas)])
            self.csv.append({"prueba": "1_base", "caso": e.nombre, "lotes_ok": r.ind.lotes_completados, "cierre_min": r.ind.makespan_min,
                             "lead_min": r.ind.lead_time_prom_min, "a_tiempo_pct": r.ind.pedidos_a_tiempo_pct,
                             "util_flota_pct": r.indicadores["utilizacion_pct"], "alertas": len(r.alertas)})
        self.tabla(["Escenario", "Lotes ok", "Cierre (min)", "Lead time (min)", "A tiempo", "Espera transp. (min)", "Util. flota", "Alertas"], filas)
        r = self.app.simulacion.execute(self.s0.id, guardar=False)
        self.h("**Estado de las áreas (S0):**")
        self.tabla(["Área", "Puestos", "Util. %", "Carga ofrecida ρ %", "Espera media (min)", "Cola máx."],
                   [[f"{e.codigo} · {e.nombre}", e.capacidad, f(e.utilizacion_pct), f(e.carga_ofrecida_pct), f(e.espera_prom_min), e.cola_max]
                    for e in r.estados])
        cuello = max(r.estados, key=lambda e: max(e.utilizacion_pct, e.carga_ofrecida_pct or 0))
        self.md.append(f"**Lectura:** el cuello de botella es **{cuello.nombre}** (carga ofrecida {f(cuello.carga_ofrecida_pct, 0)} %, espera media "
                       f"{f(cuello.espera_prom_min, 0)} min): tiene un solo puesto. El transporte no es la restricción.")
        self.figuras["estados"] = [(e.nombre, e.utilizacion_pct, e.carga_ofrecida_pct or 0) for e in r.estados]

    def p2_replicas(self):
        self.h(f"## Prueba 2 · {self.n} réplicas con variabilidad de ±15 % en los tiempos de proceso")
        filas = []
        for e in (self.s0, self.s1):
            res, vals = self.replicas(e, variabilidad_pct=15)
            filas.append([e.nombre, ic(res["makespan"]), ic(res["lead"]), ic(res["ok"]), ic(res["tiempo"], 0), ic(res["lead1"])])
            self.csv.append({"prueba": "2_replicas", "caso": e.nombre, "cierre_media": res["makespan"].media, "lead_media": res["lead"].media,
                             "ok_media": res["ok"].media, "n": self.n})
            self.figuras.setdefault("replicas", {})[e.nombre] = vals["makespan"]
        self.tabla(["Escenario", "Cierre (min)", "Lead time (min)", "Lotes ok (%)", "Pedidos a tiempo (%)", "Lead time prioridad 1"], filas)
        self.md.append("Valores: media ± semiancho del IC 95 %. La dispersión viene de la variabilidad de los tiempos; la semilla de cada réplica es fija.")

    def p3_flota(self):
        self.h("## Prueba 3 · Tamaño de la flota (S0, 1 a 6 operarios)")
        rq = self.app.requerimientos.execute(self.s0.id, 6)
        self.tabla(["Equipos", "Util. %", "Espera (min)", "Lotes ok %", "Cierre (min)", "Cumple objetivo 75 %"],
                   [[b.recursos, f(b.utilizacion_pct), f(b.espera_prom_min, 2), f(b.completados_pct), f(b.makespan_min, 0), "✔" if b.cumple else ""]
                    for b in rq.barrido])
        for b in rq.barrido:
            self.csv.append({"prueba": "3_flota", "caso": f"{b.recursos} equipos", "util_flota_pct": b.utilizacion_pct, "cierre_min": b.makespan_min,
                             "lotes_ok_pct": b.completados_pct})
        self.md.append(f"**Equipos recomendados: {rq.recomendado}.** " + " ".join(rq.notas))
        self.figuras["flota"] = [(b.recursos, b.utilizacion_pct or 0, b.makespan_min) for b in rq.barrido]
        v = {x["prenda"]: x for x in rq.viajes_por_prenda}
        self.h("**Viajes por prenda (capacidad 25 kg):**")
        self.tabla(["Prenda", "kg/u", "u/viaje", "Viajes por traslado", "Lotes", "Viajes estimados"],
                   [[x["prenda"], x["peso_unidad_kg"], x["unidades_por_viaje"], x["viajes_por_traslado"], x["lotes"], x["viajes_estimados"]]
                    for x in rq.viajes_por_prenda])
        rc = rq.recorridos
        self.md.append(f"En el turno: {rc['viajes']} viajes cargados, {f(rc['distancia_cargada_m'], 0)} m cargado + {f(rc['distancia_vacia_m'], 0)} m vacío "
                       f"= {f(rc['distancia_total_m'], 0)} m.")

    def p4_politica(self):
        self.h(f"## Prueba 4 · Prioridad vs FIFO ({self.n} réplicas, S0)")
        filas = []
        for pol in ("PRIORIDAD", "FIFO"):
            res, vals = self.replicas(self.s0, politica=pol, variabilidad_pct=15)
            filas.append([pol, ic(res["lead1"]), ic(res["lead"]), ic(res["tiempo"], 0), ic(res["makespan"])])
            self.csv.append({"prueba": "4_politica", "caso": pol, "lead_prio1": res["lead1"].media, "lead": res["lead"].media,
                             "a_tiempo": res["tiempo"].media})
            self.figuras.setdefault("politica", {})[pol] = vals["lead1"]
        self.tabla(["Política", "Lead time del pedido urgente (min)", "Lead time medio (min)", "A tiempo (%)", "Cierre (min)"], filas)
        pr, ff = filas[0], filas[1]
        self.md.append(f"**Lectura:** la prioridad adelanta el pedido urgente ({pr[1]} min frente a {ff[1]} min con FIFO), pero el retraso no desaparece: "
                       f"se traslada a pedidos de menor prioridad (pedidos a tiempo: {pr[3]} % con prioridad frente a {ff[3]} % con FIFO). "
                       "El cierre total casi no cambia, porque el cuello de botella sigue siendo el mismo.")

    def p5_balanceo(self):
        self.h(f"## Prueba 5 · Balanceo entre Costura 1 y Costura 2 ({self.n} réplicas, S0)")
        filas = []
        for b in (True, False):
            res, _ = self.replicas(self.s0, balanceo=b, variabilidad_pct=15)
            filas.append(["Con balanceo" if b else "Sin balanceo (por turnos)", ic(res["lead"]), ic(res["makespan"]), ic(res["ok"])])
            self.csv.append({"prueba": "5_balanceo", "caso": "on" if b else "off", "lead": res["lead"].media, "cierre": res["makespan"].media})
        self.tabla(["Modo", "Lead time (min)", "Cierre (min)", "Lotes ok (%)"], filas)
        self.md.append("Las dos costuras son idénticas, por eso el efecto es pequeño. El balanceo importa cuando las alternativas son distintas o están a distancias distintas.")

    def p6_demanda(self):
        self.h("## Prueba 6 · Aumento de la demanda (S1)")
        filas = []
        for d in (60, 80, 100, 120, 140):
            r = self.correr(self.s1, factor_demanda_pct=d)
            cu = max(r.estados, key=lambda e: max(e.utilizacion_pct, e.carga_ofrecida_pct or 0))
            filas.append([f"{d} %", f"{r.ind.lotes_completados}/{r.ind.lotes}", f(r.ind.completados_pct, 0), f(r.ind.makespan_min, 0),
                          f"{cu.nombre} ({f(cu.carga_ofrecida_pct, 0)} %)", len(r.alertas)])
            self.csv.append({"prueba": "6_demanda", "caso": f"{d}%", "lotes_ok_pct": r.ind.completados_pct, "cierre_min": r.ind.makespan_min,
                             "alertas": len(r.alertas)})
        self.tabla(["Demanda", "Lotes ok", "Completado %", "Cierre (min)", "Área más cargada (ρ)", "Alertas"], filas)

    def p7_mejora(self):
        self.h(f"## Prueba 7 · Qué pasa si se agrega un segundo puesto de Bordado ({self.n} réplicas, S0)")
        antes, _ = self.replicas(self.s0, variabilidad_pct=15)
        bordado = next(e for e in self.app.layout.listar_estaciones(self.taller.id) if e.codigo == "B")
        bordado.capacidad = 2
        self.app.layout.guardar_estacion(bordado)
        despues, _ = self.replicas(self.s0, variabilidad_pct=15)
        r = self.app.simulacion.execute(self.s0.id, guardar=False)
        nuevo = max(r.estados, key=lambda e: max(e.utilizacion_pct, e.carga_ofrecida_pct or 0))
        self.tabla(["Configuración", "Lead time (min)", "Cierre (min)", "Lotes ok (%)", "A tiempo (%)"],
                   [["Bordado con 1 puesto", ic(antes["lead"]), ic(antes["makespan"]), ic(antes["ok"]), ic(antes["tiempo"], 0)],
                    ["Bordado con 2 puestos", ic(despues["lead"]), ic(despues["makespan"]), ic(despues["ok"]), ic(despues["tiempo"], 0)]])
        self.csv.append({"prueba": "7_mejora", "caso": "B=1", "lead": antes["lead"].media, "cierre": antes["makespan"].media, "ok": antes["ok"].media})
        self.csv.append({"prueba": "7_mejora", "caso": "B=2", "lead": despues["lead"].media, "cierre": despues["makespan"].media, "ok": despues["ok"].media})
        self.md.append(f"Con dos puestos de Bordado el área más cargada pasa a ser **{nuevo.nombre}** (ρ {f(nuevo.carga_ofrecida_pct, 0)} %): el cuello de botella se desplaza, "
                       "que es lo esperable al optimizar un proceso. El lead time medio sube porque ahora terminan lotes que antes quedaban sin completar "
                       "(y no entraban en el promedio): mire el % de lotes completados y de pedidos a tiempo.")
        bordado.capacidad = 1
        self.app.layout.guardar_estacion(bordado)

    # ---- salida
    def escribir(self, salida: Path):
        salida.mkdir(parents=True, exist_ok=True)
        cab = [f"# TextilFlow {VERSION} · Ejercicio práctico", "",
               f"Caso: **{self.taller.nombre}** (datos SINTÉTICOS, no son mediciones) · compilación {FECHA} · {self.n} réplicas por prueba · semillas 100–{100 + self.n - 1}.",
               "", "Reproducir: `python tools/ejercicio_practico.py`."]
        (salida / "EJERCICIO_PRACTICO.md").write_text("\n".join(cab + self.md) + "\n", encoding="utf-8")
        columnas = sorted({k for fila in self.csv for k in fila}, key=lambda k: (k not in ("prueba", "caso"), k))
        with open(salida / "ejercicio_resultados.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=columnas)
            w.writeheader()
            w.writerows(self.csv)
        try:
            self.graficos(salida)
        except ImportError:
            pass

    def graficos(self, salida: Path):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({"figure.facecolor": "#0B1220", "axes.facecolor": "#101A2E", "axes.edgecolor": "#22345A",
                             "text.color": "#E6EDF7", "axes.labelcolor": "#E6EDF7", "xtick.color": "#8FA0BC", "ytick.color": "#8FA0BC"})
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        nombres = [n for n, _, _ in self.figuras["estados"]]
        x = range(len(nombres))
        ax[0].bar([i - 0.2 for i in x], [u for _, u, _ in self.figuras["estados"]], 0.4, label="Simulada", color="#2F6BDE")
        ax[0].bar([i + 0.2 for i in x], [o for _, _, o in self.figuras["estados"]], 0.4, label="Carga ofrecida ρ", color="#F29A1F")
        ax[0].axhline(85, color="#E5484D", ls="--", lw=1)
        ax[0].set_xticks(list(x)); ax[0].set_xticklabels(nombres, rotation=35, ha="right"); ax[0].set_title("Ocupación de las áreas (%)"); ax[0].legend()
        fl = self.figuras["flota"]
        ax[1].plot([a for a, _, _ in fl], [b for _, b, _ in fl], "o-", color="#5CC8FF", label="Utilización flota %")
        ax2 = ax[1].twinx(); ax2.plot([a for a, _, _ in fl], [c for _, _, c in fl], "s-", color="#6BE3B2"); ax2.set_ylabel("Cierre (min)"); ax2.set_ylim(0, 560)
        ax[1].set_title("Más equipos: la utilización baja, el cierre no mejora"); ax[1].set_xlabel("Equipos")
        for nombre, vals in self.figuras["replicas"].items():
            ax[2].hist(vals, bins=10, alpha=0.7, label=nombre)
        ax[2].set_title("Cierre del turno en las réplicas (min)"); ax[2].legend()
        fig.tight_layout(); fig.savefig(salida / "ejercicio_graficos.png", dpi=110)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replicas", type=int, default=30)
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent.parent / "docs"))
    a = ap.parse_args()
    ej = Ejercicio(a.replicas)
    for p in (ej.p1_base, ej.p2_replicas, ej.p3_flota, ej.p4_politica, ej.p5_balanceo, ej.p6_demanda, ej.p7_mejora):
        p()
    ej.escribir(Path(a.salida))
    print((Path(a.salida) / "EJERCICIO_PRACTICO.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
