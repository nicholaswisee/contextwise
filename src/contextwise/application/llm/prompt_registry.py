from dataclasses import dataclass


@dataclass(frozen=True)
class PromptDefinition:
    name: str
    version: int
    template: str


class PromptRegistry:
    def __init__(self) -> None:
        definition = PromptDefinition(name="direct", version=1, template="{prompt}")
        self._prompts = {(definition.name, definition.version): definition}

    def render(self, name: str, version: int | None, prompt: str) -> tuple[str, int]:
        versions = [
            prompt_version for prompt_name, prompt_version in self._prompts if prompt_name == name
        ]
        if not versions:
            raise KeyError(f"unknown prompt: {name}")
        selected_version = version or max(versions)
        try:
            definition = self._prompts[(name, selected_version)]
        except KeyError as error:
            raise KeyError(f"unknown prompt: {name}") from error
        return definition.template.format(prompt=prompt), definition.version

    def list(self) -> tuple[PromptDefinition, ...]:
        return tuple(self._prompts.values())
