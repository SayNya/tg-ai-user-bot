class AiogramBotError(Exception):
    """
    Base exception for all Aiogram bot errors
    """

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"
