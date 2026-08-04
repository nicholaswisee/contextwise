import contextwise


def test_package_version_exists():
    assert hasattr(contextwise, "__version__")


def test_main_module_runs_without_error():
    import importlib

    importlib.import_module("contextwise.__main__")
    assert True
