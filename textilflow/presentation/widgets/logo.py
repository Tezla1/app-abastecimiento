"""Logo de TextilFlow (un hilo que atraviesa las áreas, con su aguja) dibujado en SVG (sin archivos externos)."""
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2F6BDE"/><stop offset="1" stop-color="#1BA39C"/>
    </linearGradient>
  </defs>
  <path d="M64 6 L116 36 V92 L64 122 L12 92 V36 Z" fill="#0B1220" stroke="url(#g)" stroke-width="7" stroke-linejoin="round"/>
  <path d="M24 78 C40 30, 58 106, 76 58 S96 40, 104 46" fill="none" stroke="#8FA0BC" stroke-width="4.5" stroke-linecap="round"/>
  <path d="M24 78 C40 30, 58 106, 76 58 S96 40, 104 46" fill="none" stroke="url(#g)" stroke-width="2" stroke-dasharray="3 6" stroke-linecap="round"/>
  <circle cx="24" cy="78" r="9" fill="#F29A1F"/><circle cx="64" cy="76" r="6" fill="#2A8FD6"/>
  <circle cx="104" cy="46" r="9" fill="#1FA971"/>
  <path d="M82 92 L98 76" stroke="#E6ECF8" stroke-width="3.5" stroke-linecap="round"/><ellipse cx="97" cy="77" rx="1.6" ry="3.4" transform="rotate(45 97 77)" fill="#0B1220" stroke="#E6ECF8" stroke-width="1.5"/>
</svg>"""


def logo_pixmap(tam: int = 64) -> QPixmap:
    img = QImage(tam, tam, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    QSvgRenderer(QByteArray(SVG.encode("utf-8"))).render(p)
    p.end()
    return QPixmap.fromImage(img)


def logo_icono() -> QIcon:
    ic = QIcon()
    for t in (16, 32, 64, 128):
        ic.addPixmap(logo_pixmap(t))
    return ic
