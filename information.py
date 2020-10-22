from random import choice
import discord
from discord.ext import commands
from bot import send_error
from bot import CustomCommandError
from bot import Colours
import pymongo as mg

CATEGORY_EMOJIS = ["🔸", "🔸", "🔸", "🔸"]

# Setting up Database
MONGO_CLIENT = mg.MongoClient("mongodb://localhost:27017")
DATABASE = MONGO_CLIENT["Emojis"]
PREFIX_LIST = DATABASE["prefixes"]
SETTINGS = DATABASE["settings"]
APPROVAL_QUEUES = DATABASE["verification_queues"]


def setup(bot):
    bot.remove_command("help")
    bot.add_cog(Information(bot))


class Information(commands.Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot
        # a list of all commands

    async def create_help_embed(self, ctx, help_category):
        """Create a help embed based on the specified parameter."""

        # create embed
        help_embed = discord.Embed(title=f"Help for {help_category.capitalize()}", colour=Colours.base)

        # if parameter is a category, list all commands in the category
        if help_category.capitalize() in self.bot.cogs:
            if help_category.lower() == "developer" and ctx.message.author.id != 554275447710548018:
                return
            else:
                random_cmd = choice(commands.Cog.get_commands(self.bot.cogs[help_category.capitalize()])).name
                help_embed.add_field(
                    name="Commands",
                    value=f"`{ctx.prefix}{('` `' + ctx.prefix + '').join(sorted([command.name for command in commands.Cog.get_commands(self.bot.cogs[help_category.capitalize()])]))}`\n\n"
                          f"🔸 You can get information on a command with `{ctx.prefix}help [command]`.")

        # not a category
        elif help_category.lower() in bot_commands.keys():

            # add -- if they exist -- details of selected command (parameter) to embed
            for key, value in bot_commands[help_category.lower()].items():
                if len(value) > 0:
                    help_embed.add_field(name=key, value=value.replace("[BOT_PREFIX]", ctx.prefix), inline=False)

        # doesnt exist
        else:
            raise CustomCommandError(f"Couldn't find the command \"{help_category}\". You can view a list of commands with `{ctx.prefix}help`.")

        # return the help embed
        return help_embed

    @commands.command(name="feedback",
                      description="Give feedback on the bot.",
                      usage="[BOT_PREFIX]feedback",
                      aliases=["fb", "suggest", "suggestion"],
                      pass_context=True)
    async def feedback(self, ctx):
        await ctx.send(embed=discord.Embed(
            colour=Colours.base,
            description="Support and general enquiries go to **[the support server](https://discord.gg/wzG9Y8s)**. "
                        "Direct feedback and bot suggestions to ruby#7777."
        ))

    @commands.command(name="invite",
                      description="Invite Emojis to your server.",
                      usage="[BOT_PREFIX]invite",
                      aliases=["inv"],
                      pass_context=True)
    async def invite(self, ctx):
        """
        Generate an invite link.

        :param ctx: context
        :return: N/A
        """
        await ctx.send(embed=discord.Embed(
            colour=Colours.base,
            description=f"**[Click here](https://discord.com/api/oauth2/authorize?client_id=749301838859337799&"
                        f"permissions=1946545248&scope=bot)** to invite me to your server."
        ))

    @commands.command(name="help",
                      description="Why are you looking at the help for the help command? You're weird.",
                      usage="[BOT_PREFIX]help`, `[BOT_PREFIX]help [category]`, or `[BOT_PREFIX]help [command]",
                      aliases=["h", "wtf", "commands"],
                      pass_context=True)
    async def _help(self, ctx, *, help_category=None):
        """
        Generate and send a help embed.

        :param ctx: context
        :param help_category: the search term (i.e. command/category to get help on)
        :return: N/A
        """

        if help_category is None:
            help_embed_categories = discord.Embed(title=f"Help", colour=Colours.base)
            count = 0

            help_embed_categories.description = "Easily manage your server's emojis."

            for category in self.bot.cogs:
                if category.lower() != "developer":
                    help_embed_categories.add_field(name="\u200b",
                                                    value=f"**{CATEGORY_EMOJIS[count]} {category}**\n"
                                                          f"`{ctx.prefix}help {category.lower()}`\n",
                                                    inline=True)
                    count += 1
                else:
                    if ctx.message.author.id == 554275447710548018:
                        help_embed_categories.add_field(name="\u200b",
                                                        value=f"**{CATEGORY_EMOJIS[count]} {category}**\n"
                                                              f"`{ctx.prefix}help {category.lower()}`\n",
                                                        inline=True)
                        count += 1

            while count % 3 != 0:
                help_embed_categories.add_field(name="\u200b",
                                                value="\u200b",
                                                inline=True)
                count += 1

            await ctx.channel.send(embed=help_embed_categories)
        else:
            help_embed = await self.create_help_embed(ctx, help_category)
            if help_embed is not None:
                await ctx.channel.send(embed=help_embed)

    @commands.command(name="stats",
                      description="Get some basic stats about what Emoji Thief is up to.",
                      usage="[BOT_PREFIX]stats",
                      aliases=["statistics", "st"],
                      pass_context=True)
    async def stats(self, ctx):
        """
        Display some simple stats about the bot's status.

        :param ctx: context
        :return: N/A
        """

        stats_embed = discord.Embed(
            title="Stats",
            colour=Colours.base
        )

        stats_embed.add_field(name="Members",
                              value=f"{len(self.bot.users)}")
        stats_embed.add_field(name="Servers",
                              value=f"{len(self.bot.guilds)}")
        stats_embed.add_field(name="Emojis",
                              value=f"{len(self.bot.emojis)}")

        await ctx.channel.send(embed=stats_embed)

    @commands.command(name="vote",
                      description="Vote for the bot daily and help it stay alive.",
                      usage="[BOT_PREFIX]vote",
                      aliases=["v", "iamverycool"],
                      pass_context=True)
    async def vote(self, ctx):
        """
        Post a vote link.

        :param ctx: context
        :return: N/A
        """

        await ctx.message.add_reaction("🧡")

        await ctx.send(embed=discord.Embed(
            description=f"**[Click here to vote!](https://top.gg/bot/749301838859337799/vote)**\n\n"
                        f"Thank you, {ctx.message.author.name}! By voting, you've unlocked `{ctx.prefix}upload` "
                        f"and `{ctx.prefix}emojify` for 24 hours.",
            colour=Colours.base
        ))

    @commands.command(name="information",
                      description="Alias for `>help information`.",
                      usage="[BOT_PREFIX]information",
                      aliases=[],
                      pass_context=True)
    async def information(self, ctx):
        await self._help(ctx, help_category="information")

    @commands.command(name="settings",
                      description="Alias for `>help settings`.",
                      usage="[BOT_PREFIX]settings",
                      aliases=["config", "configuration", "configure"],
                      pass_context=True)
    async def settings(self, ctx):
        await self._help(ctx, help_category="settings")

    @commands.command(name="emoji",
                      description="Alias for `>help emoji`.",
                      usage="[BOT_PREFIX]emoji",
                      aliases=["emojis"],
                      pass_context=True)
    async def emoji(self, ctx):
        await self._help(ctx, help_category="emoji")

    @commands.command(name="management",
                      description="Alias for `>help management`.",
                      usage="[BOT_PREFIX]management",
                      aliases=["mgmt"],
                      pass_context=True)
    async def management(self, ctx):
        await self._help(ctx, help_category="management")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Listen for errors and send an error message.
        """

        # send specific cool-down message
        if isinstance(error, commands.CommandOnCooldown):
            await send_error(ctx, f"<:redticksmall:736197216900874240> That command is on cooldown. Try again in {round(error.retry_after)} seconds.")

        # miscellaneous errors
        else:
            err = error.__cause__ if error.__cause__ is not None else error
            try:
                await send_error(ctx, f"<:redticksmall:736197216900874240> {err}", extra_info={"name": "Expected format", "value": ctx.command.usage}, full_error=error)
            except AttributeError:
                pass

    @commands.Cog.listener()
    async def on_ready(self):
        global bot_commands

        # base commmands
        bot_commands = {
            command.name: {
                "Usage": f"`{command.usage}`" if command.usage is not None else "",
                "Description": command.description,
                "Aliases": f"`{'`, `'.join(sorted(command.aliases))}`" if len(command.aliases) > 0 else ""
            } for command in self.bot.commands}

        # add command groups  (Wow this is a fucking mess)
        for command in self.bot.commands:
            try:
                # update existing entries
                bot_commands[command.name] = {
                    "Usage": f"`{command.usage}`"
                    if command.usage is not None else "",
                    "Description": command.description,
                    "Sub-commands": "`" + command.name + " " + f"`, `{command.name} ".join(
                    sorted([subcommand.name for subcommand in command.commands])) + "`",
                    "Aliases": f"`{'`, `'.join(command.aliases)}`" if len(command.aliases) > 0 else ""
                }

                # add new subcommands
                for subcommand in command.commands:
                    bot_commands[f"{command.name} {subcommand.name}"] = {
                        "Usage": f"`{subcommand.usage}`"
                        if subcommand.usage is not None else "",
                        "Description": subcommand.description,
                        "Aliases": f"`{command.name} {f'`, `{command.name} '.join(sorted(subcommand.aliases))}`"
                        if len(subcommand.aliases) > 0 else ""
                    }
            except AttributeError:
                pass
