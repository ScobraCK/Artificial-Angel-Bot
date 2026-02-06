from discord.app_commands import AppCommandError

class BotError(AppCommandError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def to_dict(self):
        return {"detail": self.message}

class BotAPIError(BotError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {self.status_code}: {self.message}")

class ContentError(ValueError):
    pass