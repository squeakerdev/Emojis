from io import BytesIO
from typing import *

import motor.motor_asyncio
from discord import Color, Embed, PartialEmoji, Emoji, Webhook
from discord.utils import get as discord_get
from discord.ext.commands import (
    Context,
    BadArgument,
    PartialEmojiConverter,
    Cog,
    command,
    has_permissions,
    CheckFailure,
    check,
    guild_only,
)
from requests import get

# Prevent IDEs removing these imports -- they see them as not used
DO_NOT_REMOVE = (Cog, command, has_permissions)

DEFAULT_PREFIX = ">"

# Set up database
mg = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
db = mg.emojis_rewrite


class CustomEmojis:
    """ Emojis used in bot responses. """

    error = e = red = "<:redticksmall:736197216900874240>"
    success = s = green = "<:greenTick:769936017230266398>"
    neutral = n = gray = "<:greyTick:769937437899489301>"
    waiting = w = typing_ = "<a:typing:734095511916773417>"
    warning = yellow = "<:warningsmall:744570500919066706>"


class Colours:
    """ Colours used in bot responses. """

    error = r = red = Color(15742004)
    success = g = green = Color(3066993)
    neutral = n = normal = base = Color(16562199)
    warn = y = yellow = Color(16707936)


class ColouredEmbed(Embed):
    """ A Discord Embed with a default colour. """

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if "colour" not in kwargs and "color" not in kwargs:
            self.colour = Colours.base


# Replace the default Embed with the customised one
Embed = ColouredEmbed


async def check_if_emoji(ctx, query: str) -> Union[PartialEmoji, None]:
    """
    Check if a string can be converted to an emoji.

    :param ctx:
    :param query: The string to check.
    :return: The result of the check: the converted Emoji if True, else False.
    """
    try:
        # Check if query can be converted to an emoji
        emoji = await PartialEmojiConverter().convert(ctx=ctx, argument=query)

        return emoji or None
    except BadArgument:  # Failed
        return None


async def get_emojis_webhook(ctx: Context) -> Webhook:
    """ Find the Emojis webhook, or create it if it doesn't exist. """
    webhooks = await ctx.channel.webhooks()
    emojis_webhook = discord_get(webhooks, name="Emojis")

    return emojis_webhook or await ctx.channel.create_webhook(name="Emojis")
