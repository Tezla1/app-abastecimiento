import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from textilflow.container import construir
from textilflow.presentation.widgets.logo import logo_icono
from textilflow.version import NOMBRE, VERSION
from textilflow.presentation.app import Aplicacion


def main() -> int:
    parser = argparse.ArgumentParser(description="TextilFlow · intralogística, optimización y simulación")
    parser.add_argument("--db", default=str(Path.home() / ".textilflow" / "textilflow.db"),
                        help="ruta del archivo SQLite (use :memory: para una sesión sin guardar)")
    args = parser.parse_args()
    if args.db != ":memory:":
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        # datos de cuando el programa se llamaba INTRABOT
        antigua = Path.home() / ".intrabot" / "intrabot.db"
        if not Path(args.db).exists() and antigua.exists():
            import shutil
            shutil.copy2(antigua, args.db)

    contenedor = construir(args.db)
    if contenedor.db.respaldo_v1:
        print(f"Aviso: la base de datos de la versión 1 era incompatible y se conservó en {contenedor.db.respaldo_v1}")
    if not contenedor.talleres.listar():
        contenedor.demo.execute()

    app = QApplication(sys.argv)
    app.setApplicationName(NOMBRE)
    app.setApplicationVersion(VERSION)
    app.setWindowIcon(logo_icono())
    aplicacion = Aplicacion(contenedor, app)
    codigo = app.exec()
    contenedor.db.close()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
