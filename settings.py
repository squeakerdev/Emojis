import discord
import pymongo as mg
from discord.ext import commands
from discord.ext.commands import has_permissions

from bot import Colours
from bot import CustomCommandError

# Setting up the Database
mgclient = mg.MongoClient("mongodb://localhost:27017")
db = mgclient["Emojis"]
prefix_list = db["prefixes"]
settings = db["settings"]
queues = db["verification_queues"]


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

        prefix_list.update({"g": str(ctx.guild.id)}, {"$set": {"g": str(ctx.guild.id), "pr": prefix}}, upsert=True)

        embed = discord.Embed(title=f"Prefix updated: {prefix}",
                              colour=Colours.success,
                              description=f"Your commands now take the format `{prefix}command` (e.g. `{prefix}help`).")

        await ctx.send(embed=embed)

        bot_user = await ctx.guild.fetch_member(749301838859337799)

        await bot_user.edit(nick=f"[{prefix}] Emojis")

    @commands.group(name="queue",
                    description=f"Configure an emoji approval queue.",
                    usage="[BOT_PREFIX]queue [sub-command] <arguments>",
                    aliases=["approval"],
                    pass_context=True)
    async def queue(self, ctx):
        if ctx.invoked_subcommand is None:
            raise CustomCommandError(f"You need to enter a sub-command.\n\n"
                                     f"**Sub-commands:** `"
                                     f"{'` `'.join(sorted([command.name for command in self.logging.commands]))}`")

    @queue.command(name="enable",
                   description=f"Enable an emoji approval queue and set the channel that approval happens in.",
                   usage="[BOT_PREFIX]queue [sub-command] <arguments>",
                   aliases=["channel"],
                   pass_context=True)
    async def enable(self, ctx, approval_channel: discord.TextChannel):
        queues.update_one({"g": str(ctx.message.guild.id)},
                          {"$set": {"queue_channel": int(approval_channel.id)}},
                          upsert=True)

        await ctx.send(embed=discord.Embed(colour=Colours.success,
                                           title="Update successful",
                                           description=f"You'll need to approve emojis that users upload in "
                                                       f"{approval_channel.mention}."))

    @commands.group(name="logging",
                    description=f"Configure logs for your server.",
                    usage="[BOT_PREFIX]logging [sub-command] <arguments>",
                    aliases=["log", "logs", "logsettings"],
                    pass_context=True)
    async def logging(self, ctx):
        if ctx.invoked_subcommand is None:
            raise CustomCommandError(f"You need to enter a sub-command.\n\n"
                                     f"**Sub-commands:** `"
                                     f"{'` `'.join(sorted([command.name for command in self.logging.commands]))}`")

    @logging.command(name="channel",
                     description="Set the logging channel.",
                     usage="[BOT_PREFIX]logging channel [channel]",
                     aliases=["ch", "#"],
                     pass_context=True)
    async def logging_channel(self, ctx, channel: discord.TextChannel):
        settings.update({"g": str(ctx.message.guild.id)}, {"$set": {"lc": str(channel.id)}}, upsert=True)
