from random import choice
import discord
from discord.ext import commands
from bot import send_error
from bot import CustomCommandError
from bot import Colours
import pymongo as mg

CATEGORY_EMOJIS = ["🔹", "🔹", "🔹", "🔹"]

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
        # help_embed.set_footer(text=help_message, icon_url=self.bot.user.avatar_url)

        # if parameter is a category, list all commands in the category
        if help_category.capitalize() in self.bot.cogs:
            if help_category.lower() == "developer" and ctx.message.author.id != 554275447710548018:
                return
            else:
                help_embed.add_field(name="Commands",
                                     value=f"`{'` `'.join(sorted([command.name for command in commands.Cog.get_commands(self.bot.cogs[help_category.capitalize()])]))}`\n\n"
                                           f"Type `{ctx.prefix}help [command]` (e.g. `{ctx.prefix}help {choice(commands.Cog.get_commands(self.bot.cogs[help_category.capitalize()])).name}`)"
                                           f" for specific help on a command.")

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

    @commands.command(name="help",
                      description="Why are you looking at the help for the help command? You're weird.",
                      usage="[BOT_PREFIX]help`, `[BOT_PREFIX]help [category]`, or `[BOT_PREFIX]help [command]",
                      aliases=["h", "wtf", "commands"],
                      pass_context=True)
    async def _help(self, ctx, *, help_category=None):
        """
        Send the help message specified in on_ready.
        """

        if help_category is None:
            help_embed_categories = discord.Embed(title=f"Help", colour=Colours.base)
            # help_embed_categories.set_footer(text=help_message, icon_url=self.bot.user.avatar_url)
            count = 0

            help_embed_categories.description = "Emojis sample text"

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
