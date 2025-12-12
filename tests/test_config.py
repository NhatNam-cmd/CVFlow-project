import importlib
import os
import shutil

import config as config_module


def test_default_db_dir_created(monkeypatch):
    """Ensure the data directory is created when using the default SQLite fallback."""
    monkeypatch.delenv("DATABASE_URI", raising=False)
    data_dir = config_module.DEFAULT_DB_DIR

    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)

    reloaded = importlib.reload(config_module)

    try:
        assert os.path.isdir(reloaded.DEFAULT_DB_DIR)
        expected_uri = f"sqlite:///{reloaded.DEFAULT_DB_PATH}"
        assert reloaded.Config.SQLALCHEMY_DATABASE_URI == expected_uri
    finally:
        if os.path.exists(reloaded.DEFAULT_DB_DIR):
            shutil.rmtree(reloaded.DEFAULT_DB_DIR)
