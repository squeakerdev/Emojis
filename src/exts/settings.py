from discord.ext.commands import Command, CommandNotFound

from src.common.common import *


def setup(bot):
    bot.add_cog(Settings(bot))


class Settings(Cog):
    def __init__(self, bot):
        self.bot = bot
