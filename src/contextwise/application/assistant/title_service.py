from contextwise.application.llm.generation_service import GenerationInput, GenerationService
from contextwise.infrastructure.conversations import ConversationRepository


class TitleService:
    def __init__(
        self,
        generation_service: GenerationService,
        repository: ConversationRepository,
        model_name: str,
    ):
        self.generation_service = generation_service
        self.repository = repository
        self.model_name = model_name

    async def generate(
        self, conversation_id: str, owner_id: str, text: str, request_id: str
    ) -> None:
        result = await self.generation_service.generate(
            GenerationInput(
                prompt=f"Create a short title for this conversation:\n{text}",
                model=self.model_name,
                max_tokens=24,
            ),
            request_id=f"{request_id}:title",
        )
        title = " ".join(result.text.split())[:256]
        if title:
            await self.repository.update_title(conversation_id, owner_id, title)
