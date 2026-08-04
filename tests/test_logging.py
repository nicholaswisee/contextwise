import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from contextwise.api.middleware import RequestIDMiddleware
from contextwise.config import Settings
from contextwise.logging_config import configure_logging


def test_logging_configures_json_formatter(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    settings = Settings()
    configure_logging(settings)
    logger = logging.getLogger("contextwise")
    logger.info("hello")
    captured = capsys.readouterr()
    assert captured.out
    record = json.loads(captured.out.strip().splitlines()[0])
    assert record["message"] == "hello"
    assert record["level"] == "INFO"


def test_request_id_middleware_adds_header():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    def read_root():
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "x-request-id" in response.headers


def test_request_id_middleware_reuses_provided_header():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    def read_root():
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/", headers={"x-request-id": "my-id"})
        assert response.headers["x-request-id"] == "my-id"
