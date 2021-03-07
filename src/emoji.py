from datetime import datetime
from io import BytesIO
from random import choice, randint
from re import sub

import asyncio
import discord.ext.commands as commands
import requests

from src.common import *


async def check_if_emoji(ctx, query: str) -> Union[discord.PartialEmoji, None]:
    """
    Check if a string can be converted to an emoji.

    :param ctx:
    :param query: The string to check.
    :return: The result of the check: the converted Emoji if True, else False.
    """
    try:
        # Check if query can be converted to an emoji
        emoji = await commands.PartialEmojiConverter().convert(ctx=ctx, argument=query)

        return emoji or None
    except commands.BadArgument:  # Failed
        return None


async def upload_emoji(
    ctx: discord.Message, name: str, url: str, post_success: bool = True
) -> discord.Emoji:
    """
    Upload a custom emoji to a guild.

    :param ctx: Context. Must be a Message.
    :param name: The name for the emoji.
    :param url: The source of the image. Must be < 256kb.
    :param post_success: [Optional] Whether or not to post a success message in the chat.
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
        await ctx.send(f"{Emojis.success} **Done!**  {new_emoji}")

    return new_emoji


def setup(bot):
    bot.add_cog(Emoji(bot))


class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="upload",
        description="Upload an emoji.",
        usage=">upload [emoji name] [url]",
        aliases=["steal"],
    )
    @commands.has_permissions(manage_emojis=True)
    async def upload(self, ctx, name, url: str = None, *, extra_args=""):
        """
        Upload an emoji from an image. There are a few options for how to do this:

            - Supply both a name and URL. They will both be used to upload the emoji directly.
            - Supply a name and an attachment image (as a file). The URL will be grabbed from the image.
            - Supply an emoji to be "stolen" in replacement of the name argument - the name and URL will be grabbed
            from this emoji.

        Any other formats are invalid and will cause an error.

        :param ctx:
        :param name: The name for the emoji.
        :param url: [Optional] The URL for the emoji's image.
        :param extra_args: [Optional] If this is present, the command is too long and should error.
        """
        # TODO: See if this code can be simplified
        # Too many arguments -- likely user tried a name like "my cool emoji" instead of "my_cool_emoji"
        if extra_args:
            raise Exception(
                "That doesn't look quite right. Make sure the emoji name is only one word."
            )

        # Both arguments are already provided :)
        if name and url:
            await upload_emoji(ctx, name, url)

        # Name specified, but no URL
        elif name and not url:

            # An attachment was uploaded, use that for the emoji URL
            if ctx.message.attachments:
                url = ctx.message.attachments[0].url
                await upload_emoji(ctx, name, url)

            # No attachments
            else:
                # Check if name is an emoji to be "stolen"
                emoji = await check_if_emoji(ctx, name)

                if emoji:
                    await upload_emoji(ctx, emoji.name, emoji.url)
                else:
                    raise Exception(
                        "That doesn't look quite right. Check `>help upload`."
                    )

    @commands.command(
        name="random",
        description="Upload a random emoji.",
        usage=">random",
    )
    @commands.has_permissions(manage_emojis=True)
    async def random(self, ctx, search: str = None):
        """
        Upload a random emoji from cache. Adding a search parameter will upload an emoji with the query in its name.

        :param ctx:
        :param search: [Optional] A search query that the emoji's name must contain.
        """
        if search:
            # Make a list of emojis that match the search
            search = search.lower()
            emojis = [e for e in self.bot.emojis if search in e.name.lower()]
        else:
            emojis = self.bot.emojis

        # Pick and upload a random emoji
        emoji = choice(emojis)
        await upload_emoji(ctx, emoji.name, emoji.url)

    @commands.command(
        name="emojify",
        description="Convert a sentence to emojis.",
        usage=">emojify [sentence]",
    )
    @commands.has_permissions(manage_emojis=True)
    async def emojify(self, ctx, *, sentence):
        """
        Convert a sentence to emojis.

        :param ctx:
        :param sentence: The sentence to convert.
        """
        # Remove invalid characters
        sanitised = sub(r"[^a-zA-Z0-9 *]*", "", sentence).lower()

        emojis = []

        # Convert each letter to an emoji
        # TODO: Add support for numbers
        for letter in sanitised:
            if letter.isalpha():
                emojis.append(":regional_indicator_%s:" % letter)
            elif letter == " ":
                emojis.append(":black_large_square:")

        await ctx.send(" ".join(emojis))
