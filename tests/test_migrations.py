from pathlib import Path


def test_alembic_ini_exists():
    assert Path("alembic.ini").exists()


def test_migrations_directory_exists():
    assert Path("src/contextwise/infrastructure/migrations").is_dir()


def test_migrations_env_py_exists():
    assert Path("src/contextwise/infrastructure/migrations/env.py").exists()


def test_initial_migration_exists():
    assert list(Path("src/contextwise/infrastructure/migrations/versions").glob("*.py"))
