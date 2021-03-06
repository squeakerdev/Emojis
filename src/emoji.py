from io import BytesIO

import discord.ext.commands as commands
import requests

from src.common import *


async def upload_emoji(
    ctx: discord.Message, name: str, url: str, post_success: bool = True
) -> discord.Emoji:
    """
    Upload a custom emoji to a guild.

    :param ctx: Context. Must be a Message.
    :param name: The name for the emoji.
    :param url: The source of the image. Must be < 256kb.
    :param post_success: Whether or not to post a success message in the chat.
    :return: The new emoji.
    """
    response = requests.get(url)

    if response.ok:
        # Store the image in BytesIO to avoid saving to disk
        emoji_bytes = BytesIO(response.content)

        # Upload the emoji to the Guild
        new_emoji = await ctx.guild.create_custom_emoji(
            name=name, image=emoji_bytes.read()
        )
    else:
        raise Exception("Couldn't fetch image (%s)." % response.status_code)

    # Post a success Embed in the chat
    if post_success:
        await ctx.send(f"{new_emoji} `:{name}:`")

    return new_emoji


def setup(bot):
    bot.add_cog(Emoji(bot))


class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
