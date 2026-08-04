from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from contextwise.config import Settings

Base = declarative_base()


class Database:
    def __init__(self, settings: Settings):
        self.engine = create_async_engine(str(settings.database_url))
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session

    async def init(self) -> None:
        pass

    async def close(self) -> None:
        await self.engine.dispose()

    async def health_check(self) -> bool:
        from sqlalchemy import text

        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
