def test_cargar_demo_dos_veces_crea_copia():
    from textilflow.container import construir
    c = construir(":memory:")
    a = c.demo.execute()
    b = c.demo.execute()
    assert a.id != b.id and b.nombre.endswith("(2)")
    assert len(c.talleres.listar()) == 2
