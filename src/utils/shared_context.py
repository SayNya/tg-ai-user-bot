from typing import Any


class AppContext:
    def __init__(self) -> None:
        self.resources: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self.resources[key] = value

    def get(self, key: str) -> Any:
        return self.resources.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.resources[key] = value

    def __getitem__(self, key: str) -> Any:
        return self.resources.get(key)

    async def cleanup(self) -> None:
        if "db_pool" in self.resources:
            db_pool = self.resources["db_pool"]
            await db_pool.close()
