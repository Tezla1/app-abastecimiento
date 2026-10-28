import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from textilflow import registro
from textilflow.presentation import arranque, errores
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
    errores.instalar()                    # a partir de aquí un error inesperado muestra un cuadro en vez de cerrar el programa
    registro.info(f"Inicio de {NOMBRE} {VERSION}")

    instancia = InstanciaUnica()
    if args.db != ":memory:":
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        if not instancia.tomar():
            return 1
        # datos de cuando el programa se llamaba INTRABOT
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
    contenedor.db.marcar_guardado()           # lo anterior no cuenta como «cambios sin guardar»
    contenedor.respaldos.marcar_abierta()

    aplicacion = Aplicacion(contenedor, app)  # noqa: F841 — debe seguir viva mientras corre la aplicación
    codigo = app.exec()
    contenedor.respaldos.marcar_cerrada()
    contenedor.db.close()
    instancia.soltar()
    registro.info("Cierre normal")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
