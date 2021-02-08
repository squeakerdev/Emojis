import asyncio
import re
from random import choice, randint

import dbl
import discord
from PIL import Image
from discord.ext.commands import has_permissions

from bot import install_emoji
from src.common import *
from src.exceptions import *


ACCEPTED_LETTERS = {
    "1": ":one:",
    "2": ":two:",
    "3": ":three:",
    "4": ":four:",
    "5": ":five:",
    "6": ":six:",
    "7": ":seven:",
    "8": ":eight:",
    "9": ":nine:",
    "0": ":ten:",
    " ": "⬛",
    "!": "❗",
    "?": "❓"
}


def setup(bot):
    bot.add_cog(Emoji(bot))


async def combine_images(base_image, new_image):
    return Image.alpha_composite(base_image, new_image)


async def mass_remove_reactions(message, emojis, member: discord.Member):
    for emoji in emojis:
        await message.remove_reaction(emoji, member)


async def mass_add_reactions(message, emojis):
    for emoji in emojis:
        await message.add_reaction(emoji)


class Emoji(commands.Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    async def browse_for_emojis(self, ctx, emoji_list, start_at_index=0, existing_search_message: discord.Message = None):
        accepted_reactions = ["⬅", "👍", "➡", "🔀"]
        sent_message = None

        def reaction_check(added_reaction):
            return added_reaction.member == ctx.message.author \
                and added_reaction.message_id == sent_message.id \
                and str(added_reaction.emoji.name) in accepted_reactions

        try:
            # pick the emoji to show
            emoji = emoji_list[start_at_index]

        except IndexError:  # emoji doesn't exist

            # search already exists, which means the user reached the end of the search results
            if existing_search_message:
                await existing_search_message.edit(embed=discord.Embed(
                    colour=Colours.fail,
                    description="<:redticksmall:736197216900874240> You reached the end of the search results."
                ))
                # remove control reactions
                await existing_search_message.clear_reactions()
                return

            # this is a new search, which means 0 results were found
            else:
                raise CustomCommandError("No results found.")

        # create the embed used in the search
        embed = discord.Embed(
            title=emoji.name,
            description="React below to add this emoji to your server.",
            colour=Colours.base
        )

        # add a footer to the embed that shows the current page number
        embed.set_footer(
            text=f"Page {start_at_index + 1} of {len(emoji_list)}", icon_url=ctx.message.author.avatar_url)

        # add a preview of the emoji
        embed.set_thumbnail(url=emoji.url)

        # add fields that show details about the target emoji
        embed.add_field(name="Name", value=f"`{emoji.name}`", inline=True)
        embed.add_field(name="Animated", value=str(
            emoji.animated), inline=True)
        embed.add_field(name="URL", value=f"[link]({emoji.url})", inline=True)

        # the message already exists
        if existing_search_message:
            sent_message = existing_search_message

            # remove any existing control reactions from the author
            await mass_remove_reactions(sent_message, accepted_reactions, ctx.message.author)

            # edit the message to show the new embed
            await existing_search_message.edit(embed=embed)

        else:
            # send the new embed to the channel
            sent_message = await ctx.send(embed=embed)

        # add control reactions if they don't already exist
        await mass_add_reactions(sent_message, accepted_reactions)

        while 1:
            try:
                # wait for the author to add a control reaction
                reaction = await self.bot.wait_for("raw_reaction_add", timeout=30.0, check=reaction_check)

            # search timed out
            except asyncio.TimeoutError:

                # edit embed to show error message
                await sent_message.edit(embed=discord.Embed(
                    colour=Colours.fail,
                    description="<:redticksmall:736197216900874240> This search timed out."
                ))

                # remove control reactions
                await sent_message.clear_reactions()
                return
            else:
                # left arrow added; go to the previous page in the search
                if reaction.emoji.name == "⬅":
                    await self.browse_for_emojis(
                        ctx=ctx,
                        emoji_list=emoji_list,
                        start_at_index=start_at_index - 1,
                        existing_search_message=sent_message
                    )
                    return

                # thumbs up added; install the current emoji
                elif reaction.emoji.name == "👍":
                    await install_emoji(
                        ctx=ctx,
                        emoji_json={"image": emoji.url, "title": emoji.name},
                        success_message="Emoji installed from search"
                    )

                # right arrow added; go to the next page in the search
                elif reaction.emoji.name == "➡":
                    await self.browse_for_emojis(
                        ctx=ctx,
                        emoji_list=emoji_list,
                        start_at_index=start_at_index + 1,
                        existing_search_message=sent_message
                    )
                    return

                # shuffle added; go to a random page in the search
                elif reaction.emoji.name == "🔀":
                    await self.browse_for_emojis(
                        ctx=ctx,
                        emoji_list=emoji_list,
                        start_at_index=randint(0, len(emoji_list) - 1),
                        existing_search_message=sent_message
                    )
                    return

    @commands.command(name="search",
                      description="Search all of the emojis that this bot can see.",
                      usage="[BOT_PREFIX]search [search term (one word)]",
                      aliases=[],
                      pass_context=True)
    @has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def search(self, ctx, *, search_term):
        search_term = search_term.replace(" ", "")
        search_results = [
            emoji for emoji in self.bot.emojis if search_term.lower() in emoji.name.lower()]

        await self.browse_for_emojis(ctx=ctx, emoji_list=search_results)

    @commands.command(name="craft",
                      description="Create an emoji from parts.",
                      usage=">craft [number 1-33] [number 1-59] [number 1-66]",
                      aliases=["make", "gen"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def craft(self, ctx, base, eyes, mouth, brows=None, extras=None):
        try:
            # convert arguments to files
            base = Image.open(
                f"./data/emoji_crafting/bases/{base}.png").convert("RGBA").resize((100, 100))
            eyes = Image.open(
                f"./data/emoji_crafting/eyes/{eyes}.png").convert("RGBA").resize((100, 100))
            mouth = Image.open(
                f"./data/emoji_crafting/mouths/{mouth}.png").convert("RGBA").resize((100, 100))

            # combine images
            emoji = await combine_images(base, mouth)
            emoji = await combine_images(emoji, eyes)

            # save image
            emoji.save(f"./data/emoji_crafting/creations/{ctx.message.id}.png")

            # convert to discord file
            with open(f"./data/emoji_crafting/creations/{ctx.message.id}.png", "rb") as file:
                to_send = discord.File(file)

        # one of the numbers is out of range
        except FileNotFoundError:
            raise CustomCommandError("One of your options is out of the valid range.\n\n"
                                     "**Required values:**\n"
                                     "**Base:** 1-33\n"
                                     "**Eyes:** 1-59\n"
                                     "**Mouth:** 1-66")

        # send file
        await ctx.send(file=to_send)

    @commands.command(name="jumbo",
                      description="View an emoji in full size.",
                      usage=">jumbo :emoji:",
                      aliases=["j", "big", "size", "sizeup"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def jumbo(self, ctx, emojis: commands.Greedy[discord.PartialEmoji]):
        """
        Return an emoji's full-size image.

        :param ctx: context
        :param emojis: an emoji or list of emojis to get the image for
        :return: N/A
        """

        # no emojis provided
        if len(emojis) == 0:
            raise CustomCommandError(
                "You need to input at least one custom emoji.")
        elif len(emojis) > 3:
            raise CustomCommandError("This command is limited to 3 emojis.")

        # embed
        embed = discord.Embed(colour=Colours.success)

        for emoji in emojis:
            # add image
            embed.set_image(url=emoji.url)

            # send embed
            await ctx.message.channel.send(embed=embed)

    @commands.command(name="random",
                      description="Add a random emoji to your server.",
                      usage=">random` or `>random [name for emoji]",
                      aliases=["rand", "randomemoji"],
                      pass_context=True)
    @has_permissions(manage_emojis=True)
    async def random(self, ctx, name_for_emoji=None):
        """
        Install a random emoji from the bot's cache.

        :param ctx: context
        :param name_for_emoji: (optional) a custom name for the emoji
        :return: N/A
        """

        # pick random emoji from cache of all emojis
        emoji = choice(self.bot.emojis)
        emoji_to_upload = {"title": emoji.name, "image": str(emoji.url)}

        # install
        if name_for_emoji is not None:
            emoji_to_upload["title"] = name_for_emoji

        await install_emoji(ctx, emoji_to_upload, success_message="Random emoji added")

    @commands.command(name="info",
                      description="Get information on an emoji.",
                      usage=">info [emoji]",
                      aliases=["?", "details", "d"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def get_emoji_info(self, ctx, emoji: discord.PartialEmoji):
        """
        Get information on an emoji from the current server.

        :param ctx: context
        :param emoji: the emoji to get information on. must be a custom emoji from the current server
        :return: N/A
        """

        # required to get user who made emoji
        try:
            emoji = await ctx.guild.fetch_emoji(emoji.id)
        except Exception:
            raise CustomCommandError(f"I can't find that emoji. Make sure it's from **this** server "
                                     f"({ctx.guild.name}).")

        # setup
        emoji_details_embed = discord.Embed(
            title=emoji.name, colour=Colours.base)
        emoji_details_embed.set_thumbnail(url=emoji.url)

        # fields
        emoji_details_embed.add_field(name="ID", value=emoji.id, inline=True)
        emoji_details_embed.add_field(
            name="Usage", value=f"`:{emoji.name}:`", inline=True)
        emoji_details_embed.add_field(
            name="Created at", value=emoji.created_at, inline=True)
        emoji_details_embed.add_field(
            name="Created by", value=emoji.user, inline=True)
        emoji_details_embed.add_field(
            name="URL", value=f"[Link]({emoji.url})", inline=True)
        emoji_details_embed.add_field(
            name="Animated", value=emoji.animated, inline=True)

        # send
        await ctx.channel.send(embed=emoji_details_embed)

    @commands.command(name="link",
                      description="Get the link to an emoji, or a list of emojis.",
                      usage=">link [emoji] <emoji> <emoji> ...",
                      aliases=["getlink"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def link(self, ctx, emojis: commands.Greedy[discord.PartialEmoji]):
        """
        Get the URL for the image of an emoji, or a list of emojis.

        :param ctx: context
        :param emojis: the list of emojis
        :return:
        """
        if len(emojis) == 0:
            raise CustomCommandError("You need to input at least one emoji .")

        embed = discord.Embed(
            colour=Colours.success,
            description=""
        )

        for emoji in emojis:
            embed.description = str(embed.description) + str(emoji.url) + "\n"

        embed.set_thumbnail(url=emojis[0].url)

        await ctx.send(embed=embed)

    @commands.command(name="steal",
                      description="Steal an emoji from another server..",
                      usage="[BOT_PREFIX]upload [name for emoji] [URL OR image attachment]",
                      aliases=[],
                      pass_context=True)
    @has_permissions(manage_emojis=True)
    async def steal(self, ctx, emoji_name):
        await self.emoji_from_url(ctx, emoji_name)

    @commands.command(name="upload",
                      description="Upload an emoji from an image, URL, or from another server.",
                      usage="[BOT_PREFIX]upload [name for emoji] [URL OR image attachment]",
                      aliases=["fromurl", "u", "url"],
                      pass_context=True)
    @has_permissions(manage_emojis=True)
    async def emoji_from_url(self, ctx, emoji_name, image=None):
        """
        Upload an emoji from a URL or image.

        :param ctx: context
        :param emoji_name: name for the emoji
        :param image: image for the emoji
        :return: N/A
        """

        # fix weird argument ordering
        if image is None:
            if len(ctx.message.attachments) == 0:
                image = emoji_name
                emoji_name = None

        image_url = None

        # user added some data (e.g. an image URL or emoji)
        if image:

            # try to convert the data to an emoji and get its URL
            try:
                image = await PARTIAL_EMOJI_CONVERTER.convert(ctx=ctx, argument=image)

                # use emoji's existing name
                if emoji_name is None:
                    emoji_name = image.name

                # set url to emoji url
                image_url = image.url

            # conversion failed; use argument as-is (probably a URL)
            except commands.BadArgument:
                image_url = image

        # no data provided, but the user uploaded a file
        elif len(ctx.message.attachments) > 0:
            image_url = ctx.message.attachments[0].url

        # install emoji
        await install_emoji(ctx, {"title": emoji_name, "image": image_url}, success_message="Emoji uploaded")

    @commands.command(name="emojify",
                      description="Convert a sentence to emojis.",
                      usage=">emojify [sentence]",
                      aliases=["e"],
                      pass_context=True)
    async def emojify(self, ctx, *, sentence=None):

        """
        Convert a sentence to emojis.
        :param ctx: context
        :param sentence: the sentence to convert
        :return: N/A
        """

        # no sentence
        if sentence is None:
            raise CustomCommandError(f"You need to enter a sentence to convert to emojis. "
                                     f"Check out `{ctx.prefix}help emojify` for more information.")

        # remove non-accepted characters
        sentence = list(filter(lambda letter_: letter_.isalpha()
                               or letter_ in ACCEPTED_LETTERS, list(sentence)))

        string_to_send = ""

        for letter in sentence:
            # A-Z
            if letter.isalpha():
                string_to_send += ":regional_indicator_{}:".format(
                    letter.lower())
            # not A-Z, but is an acceptable character
            else:
                string_to_send += ACCEPTED_LETTERS[letter]

            string_to_send += " "  # add a space between letters

        # no accepted characters
        if len(string_to_send) == 0:
            raise CustomCommandError(
                f"Make sure your sentence includes some A-Z characters.")

        # too long
        elif len(string_to_send) > 2000:
            raise CustomCommandError(
                f"Your sentence is too long when converted to emojis ({len(string_to_send)} > 2000).")

        # just right
        else:
            await ctx.send(string_to_send)

    @commands.command(name="clap",
                      description="👏YOUR👏MESSAGE👏HERE👏",
                      usage=">clap [message]",
                      aliases=["👏"],
                      pass_context=True)
    async def clap(self, ctx, *, args):
        """
        Replace spaces with the clap emoji.
        :param ctx: context
        :param args: the sentence to modify
        :return: N/A
        """

        if len(args) == 0:
            raise CustomCommandError("You need to submit a message.")

        clapped = "👏" + "👏".join(args.split()) + "👏"

        if len(clapped) > 2000:
            raise CustomCommandError(
                f"Your message needs to be shorter than 2000 characters (current length: {len(clapped)}).")

        await ctx.send(clapped)

    @commands.command(name="pfp",
                      description="Turn somebody's profile picture into an emoji.",
                      usage=">pfp [@User#1234]",
                      aliases=["avatar", "profilepic", "ava", "av", "pic"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(manage_emojis=True)
    async def pfp(self, ctx, target_user: discord.Member = None, name_for_emoji=None):
        """
        Convert somebody's pfp (profile picture) to an emoji.
        :param ctx: context
        :param target_user: the user to get the profile picture from
        :param name_for_emoji: the name for the new emoji
        :return: N/A
        """

        if target_user is None:
            target_user = ctx.message.author

        emoji_json = {
            # remove special characters from username
            "title": re.sub(r"[^\w]", "", target_user.display_name if not name_for_emoji else name_for_emoji),

            # get a low-res version of the avatar
            "image": str(target_user.avatar_url).replace("?size=1024", "?size=128")
        }

        # add the emoji
        await install_emoji(ctx, emoji_json, success_message=f"Emoji added from {target_user.display_name}'s avatar")
