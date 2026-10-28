from html import escape

from ..version import NOMBRE, VERSION

CLARO = dict(fondo="#FFFFFF", texto="#1B2638", tenue="#6B7A90", borde="#C9D3E4", cabecera="#E6ECF6",
             acento="#1F55C4", alerta="#B3261E")


def _n(v, dec=1):
    return "—" if v is None else f"{v:,.{dec}f}"


def _tabla(p, encabezados, filas, derecha=()):
    cab = "".join(f'<th align="left" bgcolor="{p["cabecera"]}">{escape(h)}</th>' for h in encabezados)
    cuerpo = ""
    for fila in filas:
        celdas = "".join(f'<td align="{"right" if i in derecha else "left"}">{c}</td>' for i, c in enumerate(fila))
        cuerpo += f"<tr>{celdas}</tr>"
    return f'<table width="100%" cellspacing="0" cellpadding="6"><tr>{cab}</tr>{cuerpo}</table>'


def informe_a_html(inf, p: dict = CLARO) -> str:
    cierres = _tabla(p, ["Área cerrada", "Motivo", "Desde", "Reabre", "¿Bloquea el paso?", "Detalle"],
        [[f"<b>{escape(c['nombre'])}</b>", escape(c["motivo"]), f"min {c['desde']:g}",
          f"min {c['hasta']:g}" if c["hasta"] else "no reabre",
          "Sí" if c["bloquea_paso"] else "No", escape(c["detalle"] or "—")] for c in inf.cierres])

    if inf.rutas:
        rutas = _tabla(p, ["Prenda · rama", "Ruta normal", "Ruta alternativa", "Metros"],
            [[escape(f"{pr} · {r}"), escape(a),
              escape(b) if ok else f'<b style="color:{p["alerta"]}">{escape(b)}</b>',
              f"{_n(d0)} → {_n(d1)}" if ok else "—"] for pr, r, a, b, d0, d1, ok in inf.rutas], (3,))
    else:
        rutas = "<p>Ninguna ruta tuvo que cambiar.</p>"

    return f"""<html><head><style>
body {{ font-family: 'Segoe UI', 'Noto Sans', sans-serif; color:{p['texto']}; background:{p['fondo']}; }}
h1 {{ font-size:19px; margin-bottom:0; }} h2 {{ font-size:14px; margin-top:16px; color:{p['acento']}; }}
td {{ border-bottom:1px solid {p['borde']}; color:{p['texto']}; }} th {{ color:{p['texto']}; }}
small {{ color:{p['tenue']}; }}
</style></head><body>
<h1>Contingencia · áreas cerradas</h1>
<small>Escenario «{escape(inf.escenario.nombre)}» · {escape(inf.generado)} · {NOMBRE} v{VERSION}</small>
<h2>Qué está cerrado y por qué</h2>{cierres}
<h2>Rutas alternativas</h2>{rutas}
</body></html>"""
