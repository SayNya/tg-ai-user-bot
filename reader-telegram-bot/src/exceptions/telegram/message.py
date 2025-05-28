from src.exceptions.base import AiogramBotError


class StateProvideError(AiogramBotError):
    def __init__(
        self,
    ) -> None:
        super().__init__(message="Provide bot state when bot_previous = True")
