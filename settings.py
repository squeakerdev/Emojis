import discord
import pymongo as mg
from discord.ext import commands
from discord.ext.commands import has_permissions

from bot import Colours
from bot import CustomCommandError

# Setting up Database
MONGO_CLIENT = mg.MongoClient("mongodb://localhost:27017")
DATABASE = MONGO_CLIENT["Emojis"]
PREFIX_LIST = DATABASE["prefixes"]
SETTINGS = DATABASE["settings"]
APPROVAL_QUEUES = DATABASE["verification_queues"]


def setup(bot):
    bot.add_cog(Settings(bot))


class Settings(commands.Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="prefix",
                      description="Change the bot's prefix.",
                      usage="[BOT_PREFIX]prefix [prefix]",
                      aliases=["changeprefix", "setprefix"],
                      pass_context=True)
    @has_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix):
        """
        Change the bot's prefix for the current server.
        :param ctx: context
        :param prefix: the prefix the user wishes to change to
        :return: N/A
        """

        PREFIX_LIST.update({"g": str(ctx.guild.id)}, {"$set": {"g": str(ctx.guild.id), "pr": prefix}}, upsert=True)

        embed = discord.Embed(title=f"Prefix updated: {prefix}",
                              colour=Colours.success,
                              description=f"Your commands now take the format `{prefix}command` (e.g. `{prefix}help`).")

        await ctx.send(embed=embed)

        bot_user = await ctx.guild.fetch_member(749301838859337799)

        await bot_user.edit(nick=f"[{prefix}] Emojis")

    @commands.group(name="replace",
                    description=f"Configure the automatic replacement of emojis in this server.",
                    usage="[BOT_PREFIX]replace [sub-command] <arguments>",
                    aliases=["nqn", "nitro"],
                    pass_context=True)
    async def replace(self, ctx):
        if ctx.invoked_subcommand is None:
            raise CustomCommandError(f"You need to enter a sub-command.\n\n"
                                     f"**Sub-commands:** `"
                                     f"{'` `'.join(sorted([command.name for command in self.replace.commands]))}`")

    @replace.command(name="enable",
                     description=f"Enable automatic replacement of emojis in this server.",
                     usage="[BOT_PREFIX]replace enable",
                     aliases=["on"],
                     pass_context=True)
    @has_permissions(manage_emojis=True, manage_guild=True)
    async def enable_replace(self, ctx):
        SETTINGS.update_one({"g": str(ctx.message.guild.id)},
                            {"$set": {"replace_emojis": True}},
                            upsert=True)

        await ctx.send(embed=discord.Embed(colour=Colours.success,
                                           title="Update successful",
                                           description=f"You can now use emojis from any server I'm in."))

    @replace.command(name="disable",
                     description=f"Disable automatic replacement of emojis in this server.",
                     usage="[BOT_PREFIX]replace disable",
                     aliases=["off"],
                     pass_context=True)
    @has_permissions(manage_emojis=True, manage_guild=True)
    async def disable_replace(self, ctx):
        SETTINGS.update_one({"g": str(ctx.message.guild.id)},
                            {"$set": {"replace_emojis": False}},
                            upsert=True)

        await ctx.send(embed=discord.Embed(colour=Colours.success,
                                           title="Update successful",
                                           description=f"I won't automatically look for unparsed emojis anymore."))

