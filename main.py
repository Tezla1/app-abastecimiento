# Diseñado y Desarrollado por Jaider Esteban Rodríguez Chiribi y Sebastián González León
# Punto de entrada de TextilFlow. Todo el arranque pasa por aquí: lee los parámetros de la línea
# de comandos, crea la aplicación Qt, instala el idioma y el aviso de errores, bloquea una segunda
# ventana, abre la base de datos, ofrece recuperar un respaldo si la sesión anterior se cortó,
# carga el taller de ejemplo la primera vez y deja la ventana principal corriendo.
# Se ejecuta con: python main.py (opción --db para usar otro archivo, o :memory: para no guardar).

import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from textilflow import registro
from textilflow.presentation import arranque, errores, idioma
from textilflow.presentation.arranque import InstanciaUnica
from textilflow.presentation.widgets.logo import logo_icono
from textilflow.version import NOMBRE, VERSION
from textilflow.presentation.app import Aplicacion


def main() -> int:
    parser = argparse.ArgumentParser(description="TextilFlow · intralogística, optimización y simulación")
    parser.add_argument("--db", default=str(registro.carpeta_datos() / "textilflow.db"),
                        help="ruta del archivo SQLite (use :memory: para una sesión sin guardar)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE)
    app.setApplicationVersion(VERSION)
    app.setWindowIcon(logo_icono())
    idioma.instalar(app)
    errores.instalar()
    registro.info(f"Inicio de {NOMBRE} {VERSION}")

    instancia = InstanciaUnica()
    if args.db != ":memory:":
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        if not instancia.tomar():
            return 1
        antigua = Path.home() / ".intrabot" / "intrabot.db"
        if not Path(args.db).exists() and antigua.exists():
            import shutil
            shutil.copy2(antigua, args.db)

    contenedor = arranque.abrir_contenedor(args.db)
    if contenedor is None:
        instancia.soltar()
        return 1
    arranque.avisar_migracion(contenedor)
    restaurado = arranque.ofrecer_recuperacion(contenedor)
    if not restaurado and not contenedor.talleres.listar():
        contenedor.demo.execute()
    contenedor.db.marcar_guardado()
    contenedor.respaldos.marcar_abierta()

    aplicacion = Aplicacion(contenedor, app)
    codigo = app.exec()
    contenedor.respaldos.marcar_cerrada()
    contenedor.db.close()
    instancia.soltar()
    registro.info("Cierre normal")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
