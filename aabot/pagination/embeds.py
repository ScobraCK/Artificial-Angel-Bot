from discord import Embed

from aabot.api.response import APIResponse

class BaseEmbed(Embed):
    def __init__(self, version, *, colour = None, color = None, title = None, type = 'rich', url = None, description = None, timestamp = None):
        super().__init__(colour=colour, color=color, title=title, type=type, url=url, description=description, timestamp=timestamp)
        self.set_footer(text=f'Master Version - {version}')
