from typing import Any, Dict


class AppContext:
    def __init__(self):
        self.resources: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self.resources[key] = value

    def get(self, key: str) -> Any:
        return self.resources.get(key)

    def __setitem__(self, key: str, value: Any):
        self.resources[key] = value

    def __getitem__(self, key: str) -> Any:
        return self.resources.get(key)

    async def cleanup(self):
        if "db_pool" in self.resources:
            db_pool = self.resources["db_pool"]
            await db_pool.close()
