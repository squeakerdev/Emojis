from src.common.common import *


def setup(bot):
    bot.add_cog(Misc(bot))


class Misc(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    @command(
        name="ping",
        description="Pong!",
        usage=">ping",
        aliases=(
            "latency",
            "pong",
        ),
    )
    async def ping(self, ctx) -> None:
        latency = str(round(self.bot.latency * 1000, 2)) + "ms"

        await ctx.send(embed=Embed(title="Pong :ping_pong: ", description=f"{latency}"))
