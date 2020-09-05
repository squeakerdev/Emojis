import re
from random import choice

import discord
import pymongo as mg
from discord.ext import commands
from discord.ext.commands import has_permissions

from bot import Colours, install_emoji
from bot import CustomCommandError
from bot import EMOJI_CONVERTER

# Setting up Database
MONGO_CLIENT = mg.MongoClient("mongodb://localhost:27017")
DATABASE = MONGO_CLIENT["Emojis"]
PREFIX_LIST = DATABASE["prefixes"]
SETTINGS = DATABASE["settings"]
APPROVAL_QUEUES = DATABASE["verification_queues"]

PARTIAL_EMOJI_CONVERTER = commands.PartialEmojiConverter()


def setup(bot):
    bot.add_cog(Emoji(bot))


class Emoji(commands.Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

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
            raise CustomCommandError("You need to input at least one custom emoji.")
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
    async def get_emoji_info(self, ctx, emoji: discord.Emoji):
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
        emoji_details_embed = discord.Embed(title=emoji.name, colour=Colours.base)
        emoji_details_embed.set_thumbnail(url=emoji.url)

        # fields
        emoji_details_embed.add_field(name="ID", value=emoji.id, inline=True)
        emoji_details_embed.add_field(name="Usage", value=f"`:{emoji.name}:`", inline=True)
        emoji_details_embed.add_field(name="Created at", value=emoji.created_at, inline=True)
        emoji_details_embed.add_field(name="Created by", value=emoji.user, inline=True)
        emoji_details_embed.add_field(name="URL", value=f"[Link]({emoji.url})", inline=True)
        emoji_details_embed.add_field(name="Animated", value=emoji.animated, inline=True)

        # send
        await ctx.channel.send(embed=emoji_details_embed)

    @commands.command(name="link",
                      description="Get the link to an emoji, or a list of emojis.",
                      usage=">link [emoji] <emoji> <emoji> ...",
                      aliases=["getlink"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def link(self, ctx, emojis: commands.Greedy[discord.Emoji]):
        """
        Get the URL for the image of an emoji, or a list of emojis.

        :param ctx: context
        :param emojis: the list of emojis
        :return:
        """
        if len(emojis) == 0:
            raise CustomCommandError("You need to input at least one emoji.")

        embed = discord.Embed(
            colour=Colours.success,
            description=""
        )

        for emoji in emojis:
            embed.description = str(embed.description) + str(emoji.url) + "\n"

        embed.set_thumbnail(url=emojis[0].url)

        await ctx.send(embed=embed)

    @commands.command(name="upload",
                      description="Upload an emoji from an image, URL, or directly through Discord.",
                      usage=">upload [name for emoji] [URL OR image attachment]",
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
