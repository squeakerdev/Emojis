from random import choice
from re import sub

from src.common.common import *


class Fun(Cog):
    __slots__ = ["bot"]

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
    @guild_only()
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

        # Disguise as the user and send on Webhook
        webhook = await get_emojis_webhook(ctx)
        await webhook.send(
            " ".join(emojis),
            username=ctx.author.display_name,
            avatar_url=ctx.author.avatar_url,
        )

        await ctx.message.delete()

    @command(
        name="random",
        description="Upload a random emoji.",
        usage=">random",
    )
    @guild_only()
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

    @command(
        name="clap",
        description="👏YOUR👏MESSAGE👏HERE👏",
        usage=">clap [message]",
        aliases=("👏",),
        pass_context=True,
    )
    async def clap(self, ctx, *, args):
        """
        Replace spaces with the clap emoji.

        :param ctx:
        :param args: The sentence to clap-ify.
        """

        if not args:
            raise Exception("You need to submit a message.")

        clapped = "👏" + "👏".join(args.split()) + "👏"

        if len(clapped) > 2000:
            raise Exception(
                "Your message needs to be shorter than 2000 characters (current length: %d)."
                % len(clapped)
            )

        await ctx.send(clapped)


def setup(bot):
    bot.add_cog(Fun(bot))
