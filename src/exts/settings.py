from src.common.common import *


class Settings(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Settings(bot))
