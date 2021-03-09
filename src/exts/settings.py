from src.common.common import *


def setup(bot):
    bot.add_cog(Settings(bot))


class Settings(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    @command(
        name="prefix",
        description="Update the bot's prefix for your server.",
        usage=">prefix [prefix]",
    )
    @has_permissions(manage_guild=True)
    async def prefix(self, ctx, prefix) -> None:
        """
        Update a guild's prefix.

        :param ctx:
        :param prefix: The new prefix.
        """
        await db.settings.update_one(
            {"id": ctx.guild.id}, {"$set": {"prefix": prefix}}, upsert=True
        )

        await ctx.send(
            embed=Embed(
                colour=Colours.success,
                description="%s Your prefix is now `%s`." % (Emojis.success, prefix),
            )
        )
