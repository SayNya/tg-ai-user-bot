from .base import DetailedAiogramBotTemplateError


class StateProvideError(DetailedAiogramBotTemplateError):
    def __init__(
        self,
    ) -> None:
        super().__init__(message="Provide bot state when bot_previous = True")
