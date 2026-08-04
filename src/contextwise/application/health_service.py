from contextwise.infrastructure.database import Database


class HealthService:
    def __init__(self, database: Database):
        self.database = database

    async def is_live(self) -> bool:
        return True

    async def is_ready(self) -> bool:
        return await self.database.health_check()
