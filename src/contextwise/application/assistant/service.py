import asyncio
import hashlib
import json
from collections.abc import AsyncGenerator
from typing import Protocol

from contextwise.application.assistant.context_builder import ContextBuilder
from contextwise.application.assistant.contracts import (
    AssistantChunkEvent,
    AssistantCompletedEvent,
    AssistantErrorEvent,
    AssistantEvent,
    AssistantMessageInput,
    ContextInspection,
    ContextSnapshot,
    Conversation,
    ConversationMessage,
    MessagePart,
    TextPart,
)
from contextwise.application.assistant.errors import (
    ActiveRequestError,
    ConversationNotFoundError,
    IdempotencyConflictError,
    InvalidAncestryError,
    MessageNotFoundError,
)
from contextwise.application.llm.contracts import LLMRequest
from contextwise.application.llm.errors import LLMError
from contextwise.application.llm.generation_service import GenerationService
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.infrastructure.conversations import ConversationRepository, GenerationClaim
from contextwise.infrastructure.invocations import InvocationRepository


class AssistantStream:
    def __init__(self, generator: AsyncGenerator[AssistantEvent, None]):
        self._generator = generator

    def __aiter__(self) -> AsyncGenerator[AssistantEvent, None]:
        return self._generator

    async def collect(self) -> list[AssistantEvent]:
        return [event async for event in self._generator]

    async def aclose(self) -> None:
        await self._generator.aclose()


class TitleGenerator(Protocol):
    async def generate(
        self, conversation_id: str, owner_id: str, text: str, request_id: str
    ) -> None: ...


class AssistantService:
    def __init__(
        self,
        repository: ConversationRepository,
        invocation_repository: InvocationRepository,
        generation_service: GenerationService,
        prompt_registry: PromptRegistry,
        model_registry: ModelRegistry,
        context_budget: int,
        output_reserve: int,
        context_builder: ContextBuilder | None = None,
        title_service: TitleGenerator | None = None,
    ):
        self.repository = repository
        self.invocation_repository = invocation_repository
        self.generation_service = generation_service
        self.prompt_registry = prompt_registry
        self.model_registry = model_registry
        self.context_builder = context_builder or ContextBuilder()
        self.context_budget = context_budget
        self.output_reserve = output_reserve
        self.title_service = title_service

    async def create_conversation(self, owner_id: str) -> Conversation:
        return await self.repository.create_conversation(owner_id)

    async def list_conversations(self, owner_id: str) -> tuple[Conversation, ...]:
        return await self.repository.list_owned(owner_id)

    async def get_conversation(self, conversation_id: str, owner_id: str) -> Conversation:
        conversation = await self.repository.get_owned(conversation_id, owner_id)
        if conversation is None:
            raise ConversationNotFoundError("conversation not found")
        return conversation

    async def list_messages(
        self, conversation_id: str, owner_id: str
    ) -> tuple[ConversationMessage, ...]:
        await self.get_conversation(conversation_id, owner_id)
        return await self.repository.list_messages(conversation_id, owner_id)

    async def get_message(self, message_id: str, owner_id: str) -> ConversationMessage:
        message = await self.repository.get_message(message_id, owner_id)
        if message is None:
            raise MessageNotFoundError("message not found")
        return message

    async def send_message(
        self,
        input: AssistantMessageInput,
        owner_id: str,
        request_id: str,
        idempotency_key: str | None = None,
        conversation_id: str | None = None,
    ) -> AssistantStream:
        selected_conversation_id = conversation_id or input.conversation_id
        if selected_conversation_id is None:
            raise ConversationNotFoundError("conversation_id is required")
        return await self._start_generation(
            conversation_id=selected_conversation_id,
            owner_id=owner_id,
            request_id=request_id,
            idempotency_key=idempotency_key or request_id,
            parts=input.parts,
            model_name=input.model or self.generation_service.primary_model,
            prompt_version=input.prompt_version,
            temperature=input.temperature,
            max_tokens=input.max_tokens,
            regenerate_message_id=None,
        )

    async def regenerate(
        self, assistant_message_id: str, owner_id: str, idempotency_key: str, request_id: str
    ) -> AssistantStream:
        original = await self.get_message(assistant_message_id, owner_id)
        if original.role != "assistant" or original.parent_id is None:
            raise InvalidAncestryError("regeneration requires an assistant message with a parent")
        user_message = await self.get_message(original.parent_id, owner_id)
        if user_message.role != "user":
            raise InvalidAncestryError("regeneration parent must be a user message")
        settings = original.request_settings or {}
        temperature = settings.get("temperature")
        max_tokens = settings.get("max_tokens")
        return await self._start_generation(
            conversation_id=original.conversation_id,
            owner_id=owner_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
            parts=user_message.parts,
            model_name=original.model_name or self._model_name_for_model(original.model),
            prompt_version=original.prompt_version,
            temperature=temperature if isinstance(temperature, (int, float)) else None,
            max_tokens=max_tokens if isinstance(max_tokens, int) else None,
            regenerate_message_id=assistant_message_id,
        )

    async def branch(self, message_id: str, owner_id: str) -> Conversation:
        message = await self.get_message(message_id, owner_id)
        return await self.repository.copy_ancestry(message.conversation_id, message.id, owner_id)

    async def inspect_context(
        self, conversation_id: str, message_id: str, owner_id: str
    ) -> ContextInspection:
        await self.get_conversation(conversation_id, owner_id)
        message = await self.get_message(message_id, owner_id)
        if message.conversation_id != conversation_id or message.invocation_id is None:
            raise InvalidAncestryError("message has no persisted invocation context")
        invocation = await self.invocation_repository.get(message.invocation_id)
        if invocation is None or invocation.context_snapshot is None:
            raise InvalidAncestryError("message has no persisted invocation context")
        snapshot = ContextSnapshot.model_validate(invocation.context_snapshot)
        return ContextInspection(
            conversation_id=conversation_id,
            message_id=message_id,
            invocation_id=message.invocation_id,
            snapshot=snapshot,
        )

    async def count_assistant_messages(self, conversation_id: str, owner_id: str) -> int:
        return await self.repository.count_assistant_messages(conversation_id, owner_id)

    async def _start_generation(
        self,
        conversation_id: str,
        owner_id: str,
        request_id: str,
        idempotency_key: str,
        parts: tuple[MessagePart, ...],
        model_name: str,
        prompt_version: int | None,
        temperature: float | None,
        max_tokens: int | None,
        regenerate_message_id: str | None,
    ) -> AssistantStream:
        model = self.model_registry.get(model_name)
        prompt = self.prompt_registry.get_system_prompt(prompt_version)
        request_settings: dict[str, object] = {
            "temperature": temperature,
            "max_tokens": max_tokens or self.output_reserve,
        }
        fingerprint = self._fingerprint(
            conversation_id,
            regenerate_message_id,
            parts,
            model_name,
            prompt.version,
            temperature,
            max_tokens,
        )
        if regenerate_message_id is None:
            claim = await self.repository.claim_generation(
                conversation_id,
                idempotency_key,
                fingerprint,
                owner_id,
                parts,
                model=model.model,
                model_name=model_name,
                provider=model.provider,
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                request_settings=request_settings,
            )
        else:
            claim = await self.repository.claim_regeneration(
                regenerate_message_id,
                idempotency_key,
                fingerprint,
                owner_id,
                model=model.model,
                model_name=model_name,
                provider=model.provider,
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                request_settings=request_settings,
            )
        if claim.replay:
            if claim.request_fingerprint != fingerprint:
                raise IdempotencyConflictError("idempotency key was reused with different input")
            if claim.status == "streaming":
                raise ActiveRequestError("request is already active")
            return AssistantStream(self._replay(claim, owner_id))

        ancestry = await self.repository.get_ancestry(claim.user_message_id, owner_id)
        try:
            built = self.context_builder.build(
                prompt.template,
                ancestry,
                self.context_budget,
                self.output_reserve,
            )
        except Exception as error:
            await self.repository.mark_terminal(
                claim.request_id, "failed", owner_id, self._error_code(error)
            )
            raise

        request = LLMRequest(
            model=model.model,
            messages=built.messages,
            temperature=temperature,
            max_tokens=max_tokens or self.output_reserve,
        )
        snapshot = ContextSnapshot(
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            model_name=model_name,
            provider=model.provider,
            model=model.model,
            temperature=temperature,
            max_tokens=max_tokens or self.output_reserve,
            provider_messages=built.messages,
            selected_message_ids=built.selected_message_ids,
            estimated_input_tokens=built.estimated_input_tokens,
            truncated=built.truncated,
        )
        invocation_id = await self.invocation_repository.create_started(
            request_id=request_id,
            provider=model.provider,
            model=model.model,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            conversation_id=conversation_id,
            assistant_message_id=claim.assistant_message_id,
            context_snapshot=dict(snapshot.model_dump(mode="json")),
            selected_message_ids=built.selected_message_ids,
        )
        await self.repository.attach_invocation(claim.request_id, owner_id, invocation_id)
        return AssistantStream(
            self._stream(
                claim,
                owner_id,
                request,
                model_name,
                invocation_id,
                parts,
            )
        )

    async def _stream(
        self,
        claim: GenerationClaim,
        owner_id: str,
        request: LLMRequest,
        model_name: str,
        invocation_id: str,
        parts: tuple[MessagePart, ...],
    ) -> AsyncGenerator[AssistantEvent, None]:
        terminal = False
        provider_stream = self.generation_service.stream_request(
            request,
            request_id=claim.request_id,
            invocation_id=invocation_id,
            model_name=model_name,
        )
        try:
            async for chunk in provider_stream:
                if chunk.invocation_id is not None:
                    await self.repository.mark_terminal(claim.request_id, "completed", owner_id)
                    terminal = True
                    await self._maybe_title(claim, owner_id, parts)
                    yield AssistantCompletedEvent(
                        conversation_id=claim.conversation_id,
                        message_id=claim.assistant_message_id,
                        invocation_id=invocation_id,
                    )
                elif chunk.text:
                    await self.repository.append_assistant_text(
                        claim.assistant_message_id, chunk.text, owner_id
                    )
                    yield AssistantChunkEvent(text=chunk.text)
        except asyncio.CancelledError:
            await self.repository.mark_terminal(
                claim.request_id, "cancelled", owner_id, "cancelled"
            )
            terminal = True
            raise
        except LLMError as error:
            await self.repository.mark_terminal(claim.request_id, "failed", owner_id, error.code)
            terminal = True
            yield AssistantErrorEvent(
                code=error.code,
                conversation_id=claim.conversation_id,
                message_id=claim.assistant_message_id,
                invocation_id=invocation_id,
            )
        except Exception as error:
            await self.repository.mark_terminal(
                claim.request_id, "failed", owner_id, self._error_code(error)
            )
            terminal = True
            yield AssistantErrorEvent(
                code=self._error_code(error),
                conversation_id=claim.conversation_id,
                message_id=claim.assistant_message_id,
                invocation_id=invocation_id,
            )
        finally:
            await provider_stream.aclose()
            if not terminal:
                await self.repository.mark_terminal(
                    claim.request_id, "cancelled", owner_id, "cancelled"
                )

    async def _replay(
        self, claim: GenerationClaim, owner_id: str
    ) -> AsyncGenerator[AssistantEvent, None]:
        message = await self.get_message(claim.assistant_message_id, owner_id)
        if claim.status == "completed":
            text = self._message_text(message)
            if text:
                yield AssistantChunkEvent(text=text)
            yield AssistantCompletedEvent(
                conversation_id=claim.conversation_id,
                message_id=claim.assistant_message_id,
                invocation_id=claim.invocation_id or "",
            )
            return
        yield AssistantErrorEvent(
            code=claim.error_code or claim.status,
            conversation_id=claim.conversation_id,
            message_id=claim.assistant_message_id,
            invocation_id=claim.invocation_id,
        )

    async def _maybe_title(
        self, claim: GenerationClaim, owner_id: str, parts: tuple[TextPart | object, ...]
    ) -> None:
        if self.title_service is None:
            return
        text = "\n".join(part.text for part in parts if isinstance(part, TextPart))
        try:
            await self.title_service.generate(
                claim.conversation_id, owner_id, text, claim.request_id
            )
        except Exception:
            return

    def _model_name_for_model(self, model: str | None) -> str:
        if model is None:
            return self.generation_service.primary_model
        for definition in self.model_registry.list():
            if definition.model == model or definition.name == model:
                return definition.name
        raise InvalidAncestryError("original model is no longer registered")

    @staticmethod
    def _message_text(message: ConversationMessage) -> str:
        return "\n".join(part.text for part in message.parts if isinstance(part, TextPart))

    @staticmethod
    def _fingerprint(
        conversation_id: str,
        regenerate_message_id: str | None,
        parts: tuple[MessagePart, ...],
        model_name: str,
        prompt_version: int,
        temperature: float | None,
        max_tokens: int | None,
    ) -> str:
        payload = {
            "conversation_id": conversation_id,
            "regenerate_message_id": regenerate_message_id,
            "parts": [part.model_dump(mode="json") for part in parts],
            "model": model_name,
            "prompt_version": prompt_version,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @staticmethod
    def _error_code(error: Exception) -> str:
        if isinstance(error, LLMError):
            return error.code
        return getattr(error, "code", "provider_error")
