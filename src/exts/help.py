from discord.ext.commands import Command, CommandNotFound

from src.common.common import *


def setup(bot):
    cog = Help(bot)
    bot.add_cog(cog)


class Help(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_help_embed = Embed()

    async def create_help_embed(self, ctx) -> Embed:
        """ Create the top-level help Embed (list of commands). """
        embed = Embed(title="Commands")

        # A list of cogs with an extra "Other" cog for uncategorised commands
        cogs = list(self.bot.cogs) + ["Other"]

        command_list = {cog: [] for cog in cogs}

        # Loop through each command and add it to the dictionary
        for cmd in self.bot.walk_commands():
            cmd_usage = ctx.prefix + cmd.name

            if cmd.cog is not None:
                command_list[type(cmd.cog).__name__].append(cmd_usage)
            else:
                command_list["Other"].append(cmd_usage)

        # Add each cog's commands to the embed as a new field
        for name, commands in command_list.items():
            embed.add_field(
                name=name, value="```\n%s\n```" % "\n".join(sorted(commands))
            )  # Code block

        return embed

    async def get_command_info(self, command_name) -> Command:
        """
        Get information on a command.

        :param command_name: The command name to look up.
        :return: The Command object of the command found.
        """
        cmd = self.bot.get_command(command_name)

        if not cmd:
            raise CommandNotFound("That command (`%s`) doesn't exist." % command_name)

        return cmd

    @command(
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
            command_ = await self.get_command_info(command_name)

            embed = (
                Embed(title=command_name.lower())
                .add_field(name="Description", value=command_.description or "None")
                .add_field(name="Usage", value="`%s`" % command_.usage or "None")
            )

            await ctx.send(embed=embed)
        # Get a list of commands
        else:
            await ctx.send(embed=await self.create_help_embed(ctx))
