import json
from dataclasses import dataclass

from contextwise.config import Settings


@dataclass(frozen=True)
class ModelDefinition:
    name: str
    provider: str
    model: str
    capabilities: frozenset[str]


class ModelRegistry:
    def __init__(self, models: tuple[ModelDefinition, ...]):
        self._models = {model.name: model for model in models}

    @classmethod
    def from_settings(cls, settings: Settings) -> "ModelRegistry":
        models = [
            ModelDefinition(
                name="fake-default",
                provider="fake",
                model="fake-default",
                capabilities=frozenset({"stream", "structured", "text"}),
            )
        ]
        if settings.llm_models_json:
            configured_models = json.loads(settings.llm_models_json)
            for configured_model in configured_models:
                models.append(
                    ModelDefinition(
                        name=configured_model["name"],
                        provider=configured_model["provider"],
                        model=configured_model["model"],
                        capabilities=frozenset(configured_model["capabilities"]),
                    )
                )
        return cls(tuple(models))

    def get(self, name: str) -> ModelDefinition:
        try:
            return self._models[name]
        except KeyError as error:
            raise KeyError(f"unknown model: {name}") from error

    def list(self) -> tuple[ModelDefinition, ...]:
        return tuple(self._models.values())
