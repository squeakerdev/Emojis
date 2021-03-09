from random import randint
from re import sub

import asyncio
from discord import Member, User, Message
from discord.ext.commands import cooldown, BucketType

from src.common.common import *


class Utility(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    @command(
        name="upload",
        description="Upload an emoji.",
        usage=">upload [emoji name] [url]",
        aliases=["steal"],
    )
    @has_permissions(manage_emojis=True)
    async def upload(self, ctx, name, url: str = None, *, extra_args="") -> None:
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

    @command(
        name="pfp",
        description="Turn a profile pic into an emoji.",
        usage=">pfp [@user]",
        aliases=(
            "avatar",
            "pic",
        ),
    )
    @has_permissions(manage_emojis=True)
    async def pfp(self, ctx, user: Union[Member, User] = None) -> None:
        """
        Convert a profile picture to an emoji.

        :param ctx:
        :param user: [Optional] The target user. Omitting will run the command for the message author.
        """

        if not user:
            user = ctx.author

        # Remove invalid characters
        name = sub(r"[^a-zA-Z0-9]", "", user.name)

        await upload_emoji(ctx, name, user.avatar_url)

    @command(name="search", description="Search for an emoji.", usage=">search [query]")
    @has_permissions(manage_emojis=True)
    @cooldown(1, 30, BucketType.user)
    async def search(self, ctx, query, page_count=0):
        def check(reaction) -> bool:
            """ Check if the reaction added is valid. """
            return reaction.member.id == ctx.author.id

        async def browse(emojis: list, page: int, existing_msg: Message = None) -> None:
            """
            Create and manage an emoji browser.

            :param emojis: The list of emojis to choose from.
            :param page: The current page number of the browser.
            :param existing_msg: [Optional] The Message of the current browser. If present, edits the existing message
            instead of posting a new one.
            """

            # Pick the Emoji and create the search Embed
            emoji = emojis[page]
            embed_ = (
                Embed(
                    title="Page %s / %s" % (page + 1, len(emojis)),
                    description="`:%s:`" % emoji.name,
                )
                .set_thumbnail(url=emoji.url)
                .set_author(icon_url=ctx.author.avatar_url, name=ctx.author.name)
            )

            # If no message exists, send the Embed to the chat
            if not existing_msg:
                sent_msg = await ctx.send(embed=embed_)

                for reaction in ("⬅", "👍", "➡", "🔀"):
                    await sent_msg.add_reaction(reaction)

            # If a message does exist, edit it with the new Embed
            else:
                sent_msg = existing_msg
                await sent_msg.edit(embed=embed_)

            try:
                # Wait for a reaction to be added
                # Times out after 30 seconds and must be a valid emoji (⬅/👍/➡/🔀)
                reaction = await self.bot.wait_for(
                    "raw_reaction_add", timeout=30.0, check=check
                )
            except asyncio.TimeoutError:
                await sent_msg.edit(
                    embed=Embed(
                        colour=Colours.error,
                        description="%s This search timed out." % Emojis.error,
                    )
                )
            else:
                reaction = reaction.emoji.name

                # Reaction controls:
                #   - ⬅ Previous page
                #   - 👍 Upload current emoji
                #   - ➡ Next page
                #   - 🔀 Random page
                if reaction == "⬅":
                    if page != 0:
                        page -= 1
                elif reaction == "👍":
                    await upload_emoji(ctx, emoji.name, emoji.url)
                elif reaction == "➡":
                    if page != len(emojis) - 1:
                        page += 1
                elif reaction == "🔀":
                    page = randint(0, len(emojis) - 1)

                # Update Embed to reflect new page
                await sent_msg.remove_reaction(reaction, ctx.author)
                await browse(emojis, page, existing_msg=sent_msg)

        # Search for results in the emoji cache
        query = query.lower()
        search_results = [e for e in self.bot.emojis if query in e.name.lower()]

        if len(search_results) == 0:
            raise Exception("No results. ")

        # Start browsing
        # Function is recursive
        await browse(emojis=search_results, page=page_count)


def setup(bot):
    bot.add_cog(Utility(bot))
