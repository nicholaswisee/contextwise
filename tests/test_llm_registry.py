import pytest

from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry
from contextwise.config import Settings


def settings() -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost/contextwise",
    )


def test_model_registry_exposes_the_default_fake_model():
    model = ModelRegistry.from_settings(settings()).get("fake-default")

    assert model.provider == "fake"
    assert model.model == "fake-default"
    assert model.capabilities == frozenset({"stream", "structured", "text"})


def test_model_registry_rejects_unknown_model():
    with pytest.raises(KeyError, match="unknown model"):
        ModelRegistry.from_settings(settings()).get("missing")


def test_prompt_registry_renders_the_current_prompt_version():
    rendered, version = PromptRegistry().render("direct", None, "Explain FastAPI")

    assert rendered == "Explain FastAPI"
    assert version == 1


def test_prompt_registry_rejects_unknown_prompt():
    with pytest.raises(KeyError, match="unknown prompt"):
        PromptRegistry().render("missing", None, "prompt")


def test_schema_registry_returns_registered_answer_schema():
    schema = SchemaRegistry().get("answer")

    assert schema.model_validate_json('{"answer":"typed"}').answer == "typed"


def test_schema_registry_rejects_unknown_schema():
    with pytest.raises(KeyError, match="unknown response schema"):
        SchemaRegistry().get("missing")
