from io import BytesIO
from typing import *

import motor.motor_asyncio
from discord import Color, Embed, PartialEmoji, Emoji
from discord.ext.commands import (
    Context,
    BadArgument,
    PartialEmojiConverter,
    Cog,
    command,
    has_permissions,
)
from requests import get

# Prevent IDEs removing these imports -- they see them as not used
DO_NOT_REMOVE = (Cog, command, has_permissions)

# Set up database
mg = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
db = mg.emojis_rewrite


class Emojis:
    """ Emojis used in bot responses. """

    error = e = red = "<:redticksmall:736197216900874240>"
    success = s = green = "<:greenTick:769936017230266398>"
    neutral = n = gray = "<:greyTick:769937437899489301>"
    waiting = w = typing_ = "<a:typing:734095511916773417>"


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


async def send_success(ctx, quote):
    # TODO: document
    await ctx.send(
        embed=Embed(
            colour=Colours.success, description="%s %s" % (Emojis.success, quote)
        )
    )


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


async def upload_emoji(
    ctx: Context, name: str, url: str, post_success: bool = True
) -> Emoji:
    """
    Upload a custom emoji to a guild.

    :param ctx: Context. Must be a Message.
    :param name: The name for the emoji.
    :param url: The source of the image. Must be < 256kb.
    :param post_success: [Optional] Whether or not to post a success message in the chat.
    :return: The new emoji.
    """
    response = get(url)

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
        await ctx.send(
            embed=Embed(
                colour=Colours.success,
                description="%s `:%s:`" % (Emojis.success, name),
            ).set_thumbnail(url=new_emoji.url)
        )

    return new_emoji
