def test_import_package() -> None:
    import praxicraft

    assert praxicraft.__version__ == "0.1.0"
    assert hasattr(praxicraft, "Client")
