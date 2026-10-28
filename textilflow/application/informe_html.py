from html import escape

from ..version import NOMBRE, VERSION

_NIVEL = {"ALTO": ("#B3261E", "#FBE4E2"), "MEDIO": ("#B26A00", "#FFF0D6"), "BAJO": ("#1B7A57", "#DFF3EA")}
_ESTADO = {"mejora": ("#1B7A57", "▲ mejora"), "empeora": ("#B3261E", "▼ empeora"),
           "igual": ("#6B7A90", "= igual"), "cambia": ("#6B7A90", "↔ cambia")}


def _n(v, dec=0):
    return "—" if v is None else f"{v:,.{dec}f}"


def _tabla(encabezados, filas, alinear_der=()):
    cab = "".join(f"<th>{escape(h)}</th>" for h in encabezados)
    cuerpo = ""
    for fila in filas:
        celdas = "".join(
            f'<td align="{"right" if i in alinear_der else "left"}">{c}</td>' for i, c in enumerate(fila))
        cuerpo += f"<tr>{celdas}</tr>"
    return f'<table width="100%" cellspacing="0" cellpadding="5"><tr>{cab}</tr>{cuerpo}</table>'


def informe_a_html(inf) -> str:
    color, fondo = _NIVEL[inf.nivel]
    cierres = _tabla(
        ["Área", "Motivo", "Desde", "Reapertura", "¿Bloquea el paso?", "Detalle"],
        [[f"<b>{escape(c['nombre'])}</b> ({escape(c['codigo'])})", escape(c["motivo"]), f"min {c['desde']:g}",
          f"min {c['hasta']:g}" if c["hasta"] else "sin reapertura en el turno",
          "Sí" if c["bloquea_paso"] else "No, solo no procesa", escape(c["detalle"] or "—")] for c in inf.cierres])

    filas = []
    for nombre, a, b, v, estado, dec in inf.indicadores:
        col, txt = _ESTADO[estado]
        var = "—" if v is None else f"{v:+.1f} %"
        filas.append([escape(nombre), _n(a, dec), _n(b, dec), var, f'<span style="color:{col}"><b>{txt}</b></span>'])
    indicadores = _tabla(["Indicador", "Sin cierre", "Con cierre", "Variación", ""], filas, (1, 2, 3))

    reas = ""
    if inf.reasignaciones:
        reas = ("<h3>¿A dónde se fue el trabajo?</h3>" + _tabla(
            ["Grupo", "Área", "Lotes antes", "Lotes ahora", "Unidades antes", "Unidades ahora"],
            [[escape(g), escape(a) + (' <span style="color:#B3261E">(cerrada)</span>' if cerr else ""),
              str(l0), str(l1), str(u0), str(u1)] for g, a, l0, l1, u0, u1, cerr in inf.reasignaciones],
            (2, 3, 4, 5)))

    if inf.rutas:
        rutas = ("<h3>Rutas recalculadas</h3>" + _tabla(
            ["Prenda", "Rama", "Ruta anterior", "Ruta nueva", "Metros antes", "Metros ahora"],
            [[escape(p), escape(r), escape(a), (escape(b) if ok else f'<b style="color:#B3261E">{escape(b)}</b>'),
              _n(d0, 1), _n(d1, 1)] for p, r, a, b, d0, d1, ok in inf.rutas], (4, 5)))
    else:
        rutas = "<h3>Rutas recalculadas</h3><p>Ninguna ruta tuvo que cambiar.</p>"

    afect = ""
    if inf.afectados:
        afect = _tabla(
            ["Prenda", "Pedido", "Estado", "Por qué", "Lotes", "Unidades"],
            [[escape(p), f"#{pid}", escape(est), escape(mot or "—"), str(n), str(u)]
             for p, pid, est, mot, n, u in inf.afectados[:25]], (4, 5))

    nuevas = ""
    if inf.alertas_nuevas:
        nuevas = "<h3>Alertas nuevas por este cierre</h3><ul>" + "".join(
            f"<li><b>{escape(a.nivel)}</b> · {escape(a.titulo)}</li>" for a in inf.alertas_nuevas[:12]) + "</ul>"

    recs = "".join(f"<li>{escape(r)}</li>" for r in inf.recomendaciones)

    return f"""<html><head><style>
body {{ font-family: 'Segoe UI', 'Noto Sans', sans-serif; color:#1B2638; background:#FFFFFF; }}
h1 {{ font-size:20px; margin-bottom:0; }} h2 {{ font-size:15px; margin-top:18px; color:#1F4E9E; }}
h3 {{ font-size:13px; margin-top:16px; color:#1F4E9E; }}
th {{ background:#E6ECF6; text-align:left; border-bottom:1px solid #C9D3E4; }}
td {{ border-bottom:1px solid #E3E8F1; }} small {{ color:#6B7A90; }}
</style></head><body>
<h1>Informe de contingencia · cierre de áreas</h1>
<small>Escenario «{escape(inf.escenario.nombre)}» · generado {escape(inf.generado)} · {NOMBRE} v{VERSION}</small>
<table width="100%" cellpadding="10" cellspacing="0" style="margin-top:10px"><tr>
<td bgcolor="{fondo}"><b style="color:{color}">IMPACTO {inf.nivel}</b><br>{escape(inf.resumen)}</td></tr></table>
<h2>1. Qué se cerró y por qué</h2>{cierres}
<h2>2. Cómo cambió la operación</h2>{indicadores}
<p><small>«Sin cierre» y «Con cierre» usan el mismo escenario, los mismos pedidos y la misma semilla; solo cambia el cierre.
Cuando se completan menos lotes, que baje el tiempo o la distancia no es una mejora real: se hace menos trabajo.</small></p>
<h2>3. Qué hizo el sistema</h2>{reas}{rutas}
<h2>4. Qué quedó afectado</h2>{afect or "<p>No quedó trabajo sin terminar.</p>"}{nuevas}
<h2>5. Qué se recomienda</h2><ul>{recs}</ul>
</body></html>"""
