import discord.ext.commands as commands
from src.common import *


def setup(bot):
    cog = Help(bot)
    bot.add_cog(cog)

    cog.update_command_names()


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_names = {}
        self.command_names_formatted = ""
        self.update_command_names()

    def update_command_names(self) -> None:
        """ Update the list of commands' names. """

        self.command_names = sorted(set(cmd.name for cmd in self.bot.walk_commands()))
        self.command_names_formatted = "`%s`" % "`  `".join(self.command_names)

    async def get_command_info(self, command_name) -> commands.Command:
        """
        Get information on a command.

        :param command_name: The command name to look up.
        :return: The Command object of the command found.
        """

        command = self.bot.get_command(command_name)

        if not command:
            raise commands.CommandNotFound(
                "That command (`%s`) doesn't exist." % command_name
            )

        return command

    @commands.command(
        name="help", description="Get information on the bot.", usage=">help [command]"
    )
    async def help(self, ctx, command_name=None):
        """
        Get help for the bot. Users can specify command_name to get specific help on a command, or omit for a list of
        commands.

        :param ctx:
        :param command_name: [Optional] The command name to look up.
        """

        # Get specific information on a command
        if command_name:
            command = await self.get_command_info(command_name)

            embed = (
                discord.Embed(title=command_name.lower())
                .add_field(name="Description", value=command.description or "None")
                .add_field(name="Usage", value="`%s`" % command.usage or "None")
            )

            await ctx.send(embed=embed)
        # Get a list of commands
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Commands", description=self.command_names_formatted
                )
            )
