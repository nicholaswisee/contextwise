from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from contextwise.application.assistant.contracts import Conversation as ConversationContract
from contextwise.application.assistant.contracts import ConversationMessage as MessageContract
from contextwise.application.assistant.contracts import MessagePart
from contextwise.application.assistant.errors import InvalidAncestryError
from contextwise.infrastructure.models import Conversation as ConversationModel
from contextwise.infrastructure.models import ConversationMessage as MessageModel
from contextwise.infrastructure.models import ConversationRequest


@dataclass(frozen=True)
class GenerationClaim:
    request_id: str
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    invocation_id: str | None
    status: str
    replay: bool
    request_fingerprint: str
    error_code: str | None = None


class ConversationRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_conversation(self, owner_id: str) -> ConversationContract:
        now = datetime.now(UTC)
        conversation = ConversationModel(
            id=str(uuid4()), owner_id=owner_id, created_at=now, updated_at=now
        )
        async with self.session_factory.begin() as session:
            session.add(conversation)
        return self._conversation_contract(conversation)

    async def get_owned(self, conversation_id: str, owner_id: str) -> ConversationContract | None:
        async with self.session_factory() as session:
            conversation = await self._get_conversation(session, conversation_id, owner_id)
            return self._conversation_contract(conversation) if conversation else None

    async def list_owned(self, owner_id: str) -> tuple[ConversationContract, ...]:
        async with self.session_factory() as session:
            result = await session.scalars(
                select(ConversationModel)
                .where(ConversationModel.owner_id == owner_id)
                .order_by(ConversationModel.updated_at.desc())
            )
            return tuple(self._conversation_contract(item) for item in result)

    async def list_messages(
        self, conversation_id: str, owner_id: str | None = None
    ) -> tuple[MessageContract, ...]:
        async with self.session_factory() as session:
            if owner_id is not None and not await self._get_conversation(
                session, conversation_id, owner_id
            ):
                return ()
            result = await session.scalars(
                select(MessageModel)
                .where(MessageModel.conversation_id == conversation_id)
                .order_by(MessageModel.sequence)
            )
            return tuple(self._message_contract(item) for item in result)

    async def get_message(
        self, message_id: str, owner_id: str | None = None
    ) -> MessageContract | None:
        async with self.session_factory() as session:
            message = await self._get_message_model(session, message_id, owner_id)
            return self._message_contract(message) if message else None

    async def get_ancestry(self, message_id: str, owner_id: str) -> tuple[MessageContract, ...]:
        async with self.session_factory() as session:
            current = await self._get_message_model(session, message_id, owner_id)
            if current is None:
                return ()
            ancestry: list[MessageModel] = []
            seen: set[str] = set()
            while current is not None:
                if current.id in seen:
                    raise InvalidAncestryError("message ancestry contains a cycle")
                seen.add(current.id)
                ancestry.append(current)
                if current.parent_id is None:
                    break
                current = await session.get(MessageModel, current.parent_id)
                if current is None or current.conversation_id != ancestry[0].conversation_id:
                    raise InvalidAncestryError("message ancestry leaves its conversation")
            ancestry.reverse()
            return tuple(self._message_contract(item) for item in ancestry)

    async def create_message(
        self,
        conversation_id: str,
        parent_id: str | None,
        role: Literal["user", "assistant"],
        parts: Sequence[MessagePart],
        owner_id: str | None = None,
        status: Literal["streaming", "completed", "failed", "cancelled"] = "completed",
        model: str | None = None,
        model_name: str | None = None,
        provider: str | None = None,
        prompt_name: str | None = None,
        prompt_version: int | None = None,
        request_settings: Mapping[str, object] | None = None,
    ) -> MessageContract:
        now = datetime.now(UTC)
        async with self.session_factory.begin() as session:
            conversation = await self._get_conversation(
                session, conversation_id, owner_id, for_update=True
            )
            if conversation is None:
                raise KeyError(f"unknown conversation: {conversation_id}")
            if parent_id is not None:
                parent = await session.get(MessageModel, parent_id)
                if parent is None or parent.conversation_id != conversation_id:
                    raise InvalidAncestryError("message parent is not in the conversation")
            sequence = await self._next_sequence(session, conversation_id)
            message = MessageModel(
                id=str(uuid4()),
                conversation_id=conversation_id,
                parent_id=parent_id,
                sequence=sequence,
                role=role,
                parts=[dict(part.model_dump()) for part in parts],
                status=status,
                model=model,
                model_name=model_name,
                provider=provider,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                request_settings=dict(request_settings) if request_settings else None,
                created_at=now,
                updated_at=now,
            )
            session.add(message)
            conversation.head_message_id = message.id
            conversation.updated_at = now
        return self._message_contract(message)

    async def claim_generation(
        self,
        conversation_id: str,
        idempotency_key: str,
        request_fingerprint: str,
        owner_id: str,
        parts: Sequence[MessagePart],
        *,
        model: str | None = None,
        model_name: str | None = None,
        provider: str | None = None,
        prompt_name: str | None = None,
        prompt_version: int | None = None,
        request_settings: Mapping[str, object] | None = None,
    ) -> GenerationClaim:
        async with self.session_factory.begin() as session:
            conversation = await self._get_conversation(
                session, conversation_id, owner_id, for_update=True
            )
            if conversation is None:
                raise KeyError(f"unknown conversation: {conversation_id}")
            existing = await self._get_request(
                session, conversation_id, idempotency_key, for_update=True
            )
            if existing is not None:
                return self._claim_contract(existing, replay=True)

            now = datetime.now(UTC)
            user_message = MessageModel(
                id=str(uuid4()),
                conversation_id=conversation_id,
                parent_id=conversation.head_message_id,
                sequence=await self._next_sequence(session, conversation_id),
                role="user",
                parts=[dict(part.model_dump()) for part in parts],
                status="completed",
                created_at=now,
                updated_at=now,
            )
            assistant_message = MessageModel(
                id=str(uuid4()),
                conversation_id=conversation_id,
                parent_id=user_message.id,
                sequence=user_message.sequence + 1,
                role="assistant",
                parts=[],
                status="streaming",
                model=model,
                model_name=model_name,
                provider=provider,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                request_settings=dict(request_settings) if request_settings else None,
                created_at=now,
                updated_at=now,
            )
            request = ConversationRequest(
                id=str(uuid4()),
                conversation_id=conversation_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                user_message_id=user_message.id,
                assistant_message_id=assistant_message.id,
                status="streaming",
                created_at=now,
                updated_at=now,
            )
            session.add_all([user_message, assistant_message, request])
            conversation.head_message_id = assistant_message.id
            conversation.updated_at = now
            await session.flush()
            return self._claim_contract(request, replay=False)

    async def claim_regeneration(
        self,
        assistant_message_id: str,
        idempotency_key: str,
        request_fingerprint: str,
        owner_id: str,
        *,
        model: str | None = None,
        model_name: str | None = None,
        provider: str | None = None,
        prompt_name: str | None = None,
        prompt_version: int | None = None,
        request_settings: Mapping[str, object] | None = None,
    ) -> GenerationClaim:
        async with self.session_factory.begin() as session:
            original = await self._get_message_model(session, assistant_message_id, owner_id)
            if original is None or original.role != "assistant" or original.parent_id is None:
                raise InvalidAncestryError("regeneration requires an assistant with a user parent")
            conversation = await self._get_conversation(
                session, original.conversation_id, owner_id, for_update=True
            )
            if conversation is None:
                raise KeyError(f"unknown conversation: {original.conversation_id}")
            existing = await self._get_request(
                session, conversation.id, idempotency_key, for_update=True
            )
            if existing is not None:
                return self._claim_contract(existing, replay=True)
            parent = await session.get(MessageModel, original.parent_id)
            if parent is None or parent.role != "user":
                raise InvalidAncestryError("regeneration parent must be a user message")

            now = datetime.now(UTC)
            assistant_message = MessageModel(
                id=str(uuid4()),
                conversation_id=conversation.id,
                parent_id=parent.id,
                sequence=await self._next_sequence(session, conversation.id),
                role="assistant",
                parts=[],
                status="streaming",
                model=model or original.model,
                model_name=model_name or original.model_name,
                provider=provider or original.provider,
                prompt_name=prompt_name or original.prompt_name,
                prompt_version=prompt_version or original.prompt_version,
                request_settings=(
                    dict(request_settings) if request_settings else original.request_settings
                ),
                created_at=now,
                updated_at=now,
            )
            request = ConversationRequest(
                id=str(uuid4()),
                conversation_id=conversation.id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                user_message_id=parent.id,
                assistant_message_id=assistant_message.id,
                status="streaming",
                created_at=now,
                updated_at=now,
            )
            session.add_all([assistant_message, request])
            conversation.head_message_id = assistant_message.id
            conversation.updated_at = now
            await session.flush()
            return self._claim_contract(request, replay=False)

    async def attach_invocation(self, request_id: str, owner_id: str, invocation_id: str) -> None:
        async with self.session_factory.begin() as session:
            request = await self._get_request_by_id(session, request_id, owner_id, for_update=True)
            if request is None:
                raise KeyError(f"unknown conversation request: {request_id}")
            request.invocation_id = invocation_id
            message = await session.get(MessageModel, request.assistant_message_id)
            if message is not None:
                message.invocation_id = invocation_id
                message.updated_at = datetime.now(UTC)

    async def append_assistant_text(
        self, message_id: str, text: str, owner_id: str | None = None
    ) -> None:
        if not text:
            return
        async with self.session_factory.begin() as session:
            message = await self._get_message_model(session, message_id, owner_id, for_update=True)
            if message is None:
                raise KeyError(f"unknown assistant message: {message_id}")
            current = "".join(
                str(part["text"])
                for part in message.parts
                if part.get("type") == "text" and "text" in part
            )
            message.parts = [{"type": "text", "text": current + text}]
            message.updated_at = datetime.now(UTC)

    async def mark_terminal(
        self,
        request_id: str,
        status: Literal["completed", "failed", "cancelled"],
        owner_id: str,
        error_code: str | None = None,
    ) -> None:
        async with self.session_factory.begin() as session:
            request = await self._get_request_by_id(session, request_id, owner_id, for_update=True)
            if request is None:
                raise KeyError(f"unknown conversation request: {request_id}")
            request.status = status
            request.error_code = error_code
            request.error_message = error_code
            request.updated_at = datetime.now(UTC)
            message = await session.get(MessageModel, request.assistant_message_id)
            if message is not None:
                message.status = status
                message.updated_at = datetime.now(UTC)

    async def get_request(
        self, conversation_id: str, idempotency_key: str, owner_id: str
    ) -> GenerationClaim | None:
        async with self.session_factory() as session:
            if await self._get_conversation(session, conversation_id, owner_id) is None:
                return None
            request = await self._get_request(session, conversation_id, idempotency_key)
            return self._claim_contract(request, replay=True) if request else None

    async def get_request_for_message(
        self, message_id: str, owner_id: str
    ) -> GenerationClaim | None:
        async with self.session_factory() as session:
            message = await self._get_message_model(session, message_id, owner_id)
            if message is None:
                return None
            request = await session.scalar(
                select(ConversationRequest).where(
                    ConversationRequest.assistant_message_id == message_id
                )
            )
            return self._claim_contract(request, replay=True) if request else None

    async def update_title(self, conversation_id: str, owner_id: str, title: str) -> None:
        async with self.session_factory.begin() as session:
            conversation = await self._get_conversation(
                session, conversation_id, owner_id, for_update=True
            )
            if conversation is not None and conversation.title is None:
                conversation.title = title[:256]
                conversation.updated_at = datetime.now(UTC)

    async def copy_ancestry(
        self, source_conversation_id: str, message_id: str, owner_id: str
    ) -> ConversationContract:
        async with self.session_factory.begin() as session:
            source = await self._get_conversation(
                session, source_conversation_id, owner_id, for_update=True
            )
            selected = await session.get(MessageModel, message_id)
            if source is None or selected is None or selected.conversation_id != source.id:
                raise KeyError("unknown source conversation or message")

            source_chain: list[MessageModel] = []
            seen: set[str] = set()
            current: MessageModel | None = selected
            while current is not None:
                if current.id in seen or current.status != "completed":
                    raise InvalidAncestryError("branch source must be a complete ancestry")
                seen.add(current.id)
                source_chain.append(current)
                if current.parent_id is None:
                    break
                current = await session.get(MessageModel, current.parent_id)
                if current is None or current.conversation_id != source.id:
                    raise InvalidAncestryError("branch ancestry leaves its conversation")
            source_chain.reverse()

            now = datetime.now(UTC)
            branch = ConversationModel(
                id=str(uuid4()),
                owner_id=owner_id,
                title=None,
                source_conversation_id=source.id,
                source_message_id=selected.id,
                created_at=now,
                updated_at=now,
            )
            session.add(branch)
            id_map: dict[str, str] = {}
            for sequence, original in enumerate(source_chain, start=1):
                copied = MessageModel(
                    id=str(uuid4()),
                    conversation_id=branch.id,
                    parent_id=id_map.get(original.parent_id) if original.parent_id else None,
                    sequence=sequence,
                    role=original.role,
                    parts=[dict(part) for part in original.parts],
                    status="completed",
                    model=original.model,
                    model_name=original.model_name,
                    provider=original.provider,
                    prompt_name=original.prompt_name,
                    prompt_version=original.prompt_version,
                    request_settings=dict(original.request_settings)
                    if original.request_settings
                    else None,
                    invocation_id=None,
                    source_conversation_id=source.id,
                    source_message_id=original.id,
                    created_at=original.created_at,
                    updated_at=original.updated_at,
                )
                id_map[original.id] = copied.id
                session.add(copied)
            branch.head_message_id = id_map[selected.id]
            await session.flush()
            return self._conversation_contract(branch)

    async def count_assistant_messages(self, conversation_id: str, owner_id: str) -> int:
        async with self.session_factory() as session:
            if await self._get_conversation(session, conversation_id, owner_id) is None:
                return 0
            count = await session.scalar(
                select(func.count())
                .select_from(MessageModel)
                .where(
                    MessageModel.conversation_id == conversation_id,
                    MessageModel.role == "assistant",
                )
            )
            return int(count or 0)

    @staticmethod
    async def _get_conversation(
        session: AsyncSession,
        conversation_id: str,
        owner_id: str | None,
        for_update: bool = False,
    ) -> ConversationModel | None:
        query = select(ConversationModel).where(ConversationModel.id == conversation_id)
        if owner_id is not None:
            query = query.where(ConversationModel.owner_id == owner_id)
        if for_update:
            query = query.with_for_update()
        return cast(ConversationModel | None, await session.scalar(query))

    @staticmethod
    async def _get_message_model(
        session: AsyncSession,
        message_id: str,
        owner_id: str | None,
        for_update: bool = False,
    ) -> MessageModel | None:
        query = select(MessageModel).where(MessageModel.id == message_id)
        if owner_id is not None:
            query = query.join(
                ConversationModel, ConversationModel.id == MessageModel.conversation_id
            ).where(ConversationModel.owner_id == owner_id)
        if for_update:
            query = query.with_for_update()
        return cast(MessageModel | None, await session.scalar(query))

    @staticmethod
    async def _get_request(
        session: AsyncSession,
        conversation_id: str,
        idempotency_key: str,
        for_update: bool = False,
    ) -> ConversationRequest | None:
        query = select(ConversationRequest).where(
            ConversationRequest.conversation_id == conversation_id,
            ConversationRequest.idempotency_key == idempotency_key,
        )
        if for_update:
            query = query.with_for_update()
        return cast(ConversationRequest | None, await session.scalar(query))

    @staticmethod
    async def _get_request_by_id(
        session: AsyncSession,
        request_id: str,
        owner_id: str,
        for_update: bool = False,
    ) -> ConversationRequest | None:
        query = (
            select(ConversationRequest)
            .join(ConversationModel, ConversationModel.id == ConversationRequest.conversation_id)
            .where(
                ConversationRequest.id == request_id,
                ConversationModel.owner_id == owner_id,
            )
        )
        if for_update:
            query = query.with_for_update()
        return cast(ConversationRequest | None, await session.scalar(query))

    @staticmethod
    async def _next_sequence(session: AsyncSession, conversation_id: str) -> int:
        value = await session.scalar(
            select(func.coalesce(func.max(MessageModel.sequence), 0)).where(
                MessageModel.conversation_id == conversation_id
            )
        )
        return int(value or 0) + 1

    @staticmethod
    def _claim_contract(request: ConversationRequest, replay: bool) -> GenerationClaim:
        return GenerationClaim(
            request_id=request.id,
            conversation_id=request.conversation_id,
            user_message_id=request.user_message_id,
            assistant_message_id=request.assistant_message_id,
            invocation_id=request.invocation_id,
            status=request.status,
            replay=replay,
            request_fingerprint=request.request_fingerprint,
            error_code=request.error_code,
        )

    @staticmethod
    def _conversation_contract(conversation: ConversationModel) -> ConversationContract:
        return ConversationContract.model_validate(conversation)

    @staticmethod
    def _message_contract(message: MessageModel) -> MessageContract:
        return MessageContract.model_validate(message)
