from discord.app_commands import AppCommandError

class BotError(AppCommandError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def to_dict(self):
        return {"error": self.message}
