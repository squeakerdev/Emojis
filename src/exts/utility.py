import logging
from asyncio import TimeoutError as TimeoutError_
from random import randint
from re import sub

from discord import Member, User, Message, NotFound
from discord.ext.commands import cooldown, BucketType

from src.common.common import *


class Utility(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot
        self.packs = get("https://discordemoji.com/api/packs").json()
        self.packs_embed = self.list_packs()

    def list_packs(self) -> Embed:
        """ A list of emoji packs from emoji.gg that can be downloaded. """

        list_embed = Embed(
            title=f"{len(self.packs)} emoji packs available",
            description="Type `>pack [number]` to view (example: `>pack 1`)\n",
        )

        for count, value in enumerate(self.packs, start=1):
            list_embed.description += '\n`>pack %d` -- view **"%s"**' % (
                count,
                value["name"],
            )

        return list_embed

    @command(
        name="upload",
        description="Upload an emoji.",
        usage=">upload [emoji name] [url]",
        aliases=("steal",),
    )
    @guild_only()
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
    @guild_only()
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

    @command(
        name="search",
        description="Search for an emoji.",
        usage=">search [query]",
        aliases=("browse", "find"),
    )
    @guild_only()
    @has_permissions(manage_emojis=True)
    @cooldown(1, 30, BucketType.user)
    async def search(self, ctx, query):
        """
        Search the bot cache for emojis.

        :param ctx:
        :param query: The search term that emoji names must contain.
        """

        def reaction_check(reaction) -> bool:
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
            embed = (
                Embed(
                    title="Page %s / %s" % (page + 1, len(emojis)),
                    description="`:%s:`" % emoji.name,
                )
                .set_thumbnail(url=emoji.url)
                .set_author(icon_url=ctx.author.avatar_url, name=ctx.author.name)
            )

            # If no message exists, send the Embed to the chat
            if not existing_msg:
                sent_msg = await ctx.send(embed=embed)

                for reaction in ("⬅", "👍", "➡", "🔀"):
                    await sent_msg.add_reaction(reaction)

            # If a message does exist, edit it with the new Embed
            else:
                sent_msg = existing_msg
                await sent_msg.edit(embed=embed)

            try:
                # Wait for a reaction to be added
                # Times out after 30 seconds and must be a valid emoji (⬅/👍/➡/🔀)
                reaction = await self.bot.wait_for(
                    "raw_reaction_add", timeout=30.0, check=reaction_check
                )
            except TimeoutError_:  # asyncio.TimeoutError
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
        await browse(emojis=search_results, page=0)

    @command(
        name="link",
        description="Get an emoji's URL.",
        usage=">link [emoji]",
        aliases=("url",),
    )
    async def link(self, ctx, emoji: PartialEmoji) -> None:
        """
        Get an emoji's URL.. Posts the URL to the chat.

        :param ctx:
        :param emoji: The emoji to show.
        """
        await ctx.send("<%s>" % emoji.url)

    @command(
        name="info",
        description="Get information on an emoji.",
        usage=">info [emoji]",
        aliases=("?", "details"),
    )
    @guild_only()
    @cooldown(1, 5, BucketType.user)
    async def info(self, ctx, emoji: PartialEmoji):
        """
        Get information on an emoji from the current server.

        :param ctx:
        :param emoji: The emoji to get information on. Must be a custom emoji from the current server.
        """

        # Required to get user who made emoji
        try:
            emoji = await ctx.guild.fetch_emoji(emoji.id)
        except NotFound:
            raise Exception(
                f"Can't find that emoji. Make sure it's from *this* server."
            )

        await ctx.send(
            embed=Embed(title=emoji.name)
            .set_thumbnail(url=emoji.url)
            .add_field(name="ID", value=emoji.id)
            .add_field(name="Usage", value=f"`:%s:`" % emoji.name)
            .add_field(name="Created at", value=emoji.created_at)
            .add_field(name="Created by", value=emoji.user)
            .add_field(name="URL", value=f"[Link](%s)" % emoji.url)
            .add_field(name="Animated", value=emoji.animated)
        )

    @command(
        name="pack",
        description="View an emoji pack. Use `>pack` first!",
        usage=">pack [number]",
        aliases=("packs",),
    )
    async def pack(self, ctx, pack_number: int = None):
        """
        View a specific emoji pack as listed by >packs.

        :param ctx:
        :param pack_number: The pack to view.
        """

        if not pack_number:
            await ctx.send(embed=self.packs_embed)
            return

        # Pack does not exist
        try:
            pack = self.packs[pack_number - 1]
        except IndexError:
            raise Exception(
                "That's not a valid pack. Use `>packs` to see a list of available packs."
            )

        # fields
        embed = (
            Embed(title=pack["name"], description=pack["description"])
            .add_field(name="Download", value=pack["download"])
            .set_image(url=pack["image"])
        )

        # send
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
