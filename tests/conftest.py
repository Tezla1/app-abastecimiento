import pytest

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
