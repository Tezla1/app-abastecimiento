"""Respaldos automáticos del proyecto (últimos 3) y detección de cierres incorrectos.

Cada respaldo es un archivo .rlr normal (el mismo formato de «Exportar proyecto»), así que también se puede
restaurar desde Data Manager → «Restaurar proyecto».
"""
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

MAXIMO = 3
PREFIJO = "auto_"


class Respaldos:
    def __init__(self, carpeta: Optional[Path], exportar: Callable[[str], None], restaurar: Callable[[str], None]):
        self._carpeta = Path(carpeta) if carpeta else None      # None = desactivado (p. ej. base en memoria)
        self._exportar, self._restaurar = exportar, restaurar

    @property
    def activo(self) -> bool:
        return self._carpeta is not None

    @property
    def carpeta(self) -> Optional[Path]:
        return self._carpeta

    # --- respaldos automáticos -------------------------------------------------------------------------
    def crear(self) -> Optional[Path]:
        if not self.activo:
            return None
        self._carpeta.mkdir(parents=True, exist_ok=True)
        ruta = self._carpeta / f"{PREFIJO}{datetime.now():%Y%m%d_%H%M%S}.rlr"
        self._exportar(str(ruta))
        for viejo in self.listar()[MAXIMO:]:
            try:
                viejo[0].unlink()
            except OSError:
                pass
        return ruta

    def listar(self) -> list[tuple[Path, datetime]]:
        """Respaldos existentes, del más reciente al más antiguo."""
        if not self.activo or not self._carpeta.is_dir():
            return []
        out = []
        for f in self._carpeta.glob(f"{PREFIJO}*.rlr"):
            try:
                out.append((f, datetime.strptime(f.stem[len(PREFIJO):], "%Y%m%d_%H%M%S")))
            except ValueError:
                continue
        return sorted(out, key=lambda x: x[1], reverse=True)

    def restaurar(self, ruta: Path) -> None:
        self._restaurar(str(ruta))

    # --- cierre correcto / incorrecto ------------------------------------------------------------------
    @property
    def _bandera(self) -> Optional[Path]:
        return self._carpeta / "sesion_abierta.flag" if self.activo else None

    def sesion_anterior_incorrecta(self) -> bool:
        return bool(self.activo and self._bandera.exists())

    def marcar_abierta(self) -> None:
        if self.activo:
            self._carpeta.mkdir(parents=True, exist_ok=True)
            self._bandera.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")

    def marcar_cerrada(self) -> None:
        if self.activo:
            try:
                self._bandera.unlink(missing_ok=True)
            except OSError:
                pass
