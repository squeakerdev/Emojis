from re import sub

from src.common.common import *


class Management(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    @command(
        name="rename",
        description="Rename an emoji.",
        usage=">rename [emoji] [new name]",
    )
    @guild_only()
    @has_permissions(manage_emojis=True)
    async def rename(self, ctx, emoji: Emoji, *, new_name) -> None:
        """
        Rename an emoji.

        :param ctx:
        :param emoji: The Emoji to rename. Must be from the current Guild.
        :param new_name: The new name for the emoji.
        """
        if emoji.guild_id != ctx.guild.id:
            raise Exception("That emoji isn't from this server.")

        old_name = emoji.name

        # Remove invalid characters
        new_name = sub(r"[^a-zA-Z0-9_ ]", "", new_name)
        new_name = sub(r" ", "_", new_name)

        await emoji.edit(name=new_name)
        await ctx.send_success("Emoji updated. `:%s:` -> `:%s:`" % (old_name, new_name))

    @command(
        name="delete",
        description="Delete an emoji.",
        usage=">delete [emoji]",
    )
    @has_permissions(manage_emojis=True)
    async def delete(self, ctx, emoji: Emoji) -> None:
        """
        Delete an emoji.

        :param ctx:
        :param emoji: The Emoji to delete. Must be from the current Guild.
        """
        if emoji.guild_id != ctx.guild.id:
            raise Exception("That emoji isn't from this server.")

        await emoji.delete(reason="Delete command called by %s" % ctx.author)
        await ctx.send_success("Emoji deleted.")


def setup(bot):
    bot.add_cog(Management(bot))
