import os
import tempfile

import pytest

os.environ["TEXTILFLOW_SINCRONO"] = "1"
os.environ["TEXTILFLOW_HOME"] = tempfile.mkdtemp(prefix="tf_home_")
from PyQt6.QtCore import QSettings
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp(prefix="tf_cfg_"))

from textilflow.container import construir


@pytest.fixture
def app():
    c = construir(":memory:")
    yield c
    c.db.close()


@pytest.fixture
def demo(app):
    taller = app.demo.execute()
    return app, taller
