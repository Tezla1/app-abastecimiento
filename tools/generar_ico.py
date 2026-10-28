# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Genera assets/textilflow.ico y el PNG de 256 px a partir del logo dibujado en código.
# Solo se corre a mano cuando cambia el logo; necesita Pillow.

import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtGui import QGuiApplication
from PIL import Image
from textilflow.presentation.widgets.logo import logo_pixmap

app = QGuiApplication([])
destino = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(destino, exist_ok=True)
png = os.path.join(destino, "textilflow_256.png")
logo_pixmap(256).save(png)
Image.open(png).save(os.path.join(destino, "textilflow.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
