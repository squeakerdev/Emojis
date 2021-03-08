from random import choice
from re import sub

from discord import Webhook
from discord.utils import get as discord_get

from src.common.common import *


async def get_emojis_webhook(ctx: Context) -> Webhook:
    """ Find the Emojis webhook, or create it if it doesn't exist. """
    webhooks = await ctx.channel.webhooks()
    emojis_webhook = discord_get(webhooks, name="Emojis")

    return emojis_webhook or await ctx.channel.create_webhook(name="Emojis")


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(
        name="jumbo",
        description="View an emoji in full size.",
        usage=">jumbo [emoji]",
    )
    async def jumbo(self, ctx, emoji: PartialEmoji) -> None:
        """
        View an emoji in full size. Posts the URL to the chat.

        :param ctx:
        :param emoji: The emoji to show.
        """
        await ctx.send(emoji.url)

    @command(
        name="emojify",
        description="Convert a sentence to emojis.",
        usage=">emojify [sentence]",
    )
    async def emojify(self, ctx, *, sentence) -> None:
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

        webhook = await get_emojis_webhook(ctx)
        await webhook.send(
            " ".join(emojis),
            username=ctx.author.display_name,
            avatar_url=ctx.author.avatar_url,
        )

    @command(
        name="random",
        description="Upload a random emoji.",
        usage=">random",
    )
    @has_permissions(manage_emojis=True)
    async def random(self, ctx, search: str = None) -> None:
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


def setup(bot):
    bot.add_cog(Fun(bot))
