# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Iconos SVG de la barra lateral, dibujados en código y pintados con el color del tema.

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

_ICONOS = {
    "dashboard": '<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="5" rx="2"/>'
                 '<rect x="13" y="10" width="8" height="11" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/>',
    "taller": '<path d="M3 21V10l6 4V10l6 4V6h3v15z"/><path d="M3 21h18"/><path d="M7 17h2M12 17h2M17 17h1"/>',
    "layout": '<circle cx="5" cy="6" r="2.2"/><circle cx="19" cy="6" r="2.2"/><circle cx="12" cy="18" r="2.2"/>'
              '<path d="M7 6h10M6.3 8l4.6 8M17.7 8l-4.6 8"/>',
    "modelo": '<path d="M18 4H7l6 8-6 8h11"/>',
    "robot": '<rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 8V4"/><circle cx="12" cy="3.5" r="1"/>'
             '<circle cx="9" cy="13" r="1.4"/><circle cx="15" cy="13" r="1.4"/><path d="M9 17h6M2 12v3M22 12v3"/>',
    "escenarios": '<circle cx="12" cy="12" r="9"/><path d="M10 8.5l5.5 3.5-5.5 3.5z"/>',
    "mapa": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "requisitos": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M8.5 12l2.2 2.2 4.3-4.6M8.5 18h7"/>',
    "comparacion": '<path d="M4 20V11M10 20V4M16 20V9M22 20V14"/><path d="M2 20.5h21"/>',
    "reportes": '<path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5M9 13h7M9 17h7M9 9h2"/>',
    "validacion": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "contingencias": '<path d="M12 3l10 18H2z"/><path d="M12 10v5"/><circle cx="12" cy="18" r="0.7"/>',
    "sol": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "luna": '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z"/>',
    "datos": '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "guia": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="7.5" r="0.6"/>',
}

_POR_ETIQUETA = [
    ("Dashboard", "dashboard"), ("Caracterización", "taller"), ("Layout", "layout"), ("Modelo", "modelo"),
    ("Diseño conceptual", "robot"), ("Escenarios", "escenarios"), ("Mapa", "mapa"), ("Requerimientos", "requisitos"),
    ("Comparación", "comparacion"), ("Resultados", "reportes"), ("Contingencias", "contingencias"), ("Sol", "sol"), ("Luna", "luna"), ("Validación", "validacion"),
    ("Data", "datos"), ("Guía", "guia"),
]


def clave_de(etiqueta: str) -> str:
    return next((k for pref, k in _POR_ETIQUETA if etiqueta.startswith(pref)), "dashboard")


def icono_svg(clave: str, color: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_ICONOS[clave]}</svg>')


def icono(etiqueta: str, color: str, tam: int = 20) -> QIcon:
    ic = QIcon()
    for t in (tam, tam * 2):
        img = QImage(t, t, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        QSvgRenderer(QByteArray(icono_svg(clave_de(etiqueta), color).encode("utf-8"))).render(p)
        p.end()
        ic.addPixmap(QPixmap.fromImage(img))
    return ic
