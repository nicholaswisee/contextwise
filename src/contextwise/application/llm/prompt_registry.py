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
        system_definition = PromptDefinition(
            name="system",
            version=1,
            template="You are Contextwise, a concise and helpful assistant.",
        )
        self._system_prompts = {
            (system_definition.name, system_definition.version): system_definition
        }

    def get(self, name: str, version: int | None = None) -> PromptDefinition:
        registry = self._system_prompts if name == "system" else self._prompts
        versions = [
            prompt_version for prompt_name, prompt_version in registry if prompt_name == name
        ]
        if not versions:
            raise KeyError(f"unknown prompt: {name}")
        selected_version = version or max(versions)
        try:
            return registry[(name, selected_version)]
        except KeyError as error:
            raise KeyError(f"unknown prompt: {name}") from error

    def get_system_prompt(self, version: int | None = None) -> PromptDefinition:
        return self.get("system", version)

    def render(self, name: str, version: int | None, prompt: str) -> tuple[str, int]:
        definition = self.get(name, version)
        return definition.template.format(prompt=prompt), definition.version

    def list(self) -> tuple[PromptDefinition, ...]:
        return tuple(self._prompts.values())
