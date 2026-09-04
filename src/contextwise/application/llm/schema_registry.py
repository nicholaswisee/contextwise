from pydantic import BaseModel, Field


class Answer(BaseModel):
    answer: str = Field(min_length=1)


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, type[BaseModel]] = {"answer": Answer}

    def get(self, name: str) -> type[BaseModel]:
        try:
            return self._schemas[name]
        except KeyError as error:
            raise KeyError(f"unknown response schema: {name}") from error
