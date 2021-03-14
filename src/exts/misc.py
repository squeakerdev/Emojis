from discord.ext.commands import Command, CommandNotFound, is_owner

from src.common.common import *

INVITE_URL = "https://discord.com/oauth2/authorize?client_id=749301838859337799&permissions=1946545248&scope=bot"
VOTE_URL = "https://top.gg/bot/749301838859337799/vote"
GITHUB_URL = "https://github.com/passivity/emojis"
WHATS_NEW = (
    "**The bot is back online!** We finished rebuilding the bot from the ground up to give you the best experience "
    "possible."
)


def setup(bot):
    bot.add_cog(Misc(bot))


class Misc(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot
        self.base_help_embed = Embed()
        self.bot.loop.create_task(self.create_help_embed())

    async def create_help_embed(self) -> None:
        """ Create the top-level help Embed (list of commands). """

        embed = Embed()
        embed.add_field(name="What's new?", value="⭐ %s" % WHATS_NEW, inline=False)

        # A list of cogs with an extra "Other" cog for uncategorised commands
        cogs = list(self.bot.cogs) + ["Other"]

        command_list = {cog: [] for cog in cogs}

        # Loop through each command and add it to the dictionary
        for cmd in self.bot.walk_commands():
            if not cmd.hidden:
                cmd_usage = ">" + cmd.name

                if cmd.cog is not None:
                    command_list[type(cmd.cog).__name__].append(cmd_usage)
                else:
                    command_list["Other"].append(cmd_usage)

        # Add each cog's commands to the embed as a new field
        for name, commands in command_list.items():
            if commands:
                embed.add_field(
                    name=name,
                    value="```\n%s\n```" % "\n".join(sorted(commands)),  # Code block
                )

        self.base_help_embed = embed

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
        name="help",
        description="Get information on the bot.",
        usage=">help [command]",
        aliases=("commands",),
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
            cmd = await self.get_command_info(command_name)

            embed = (
                Embed(title=command_name.lower())
                .add_field(name="Description", value=cmd.description or "None")
                .add_field(name="Usage", value="`%s`" % cmd.usage or "None")
                .add_field(
                    name="Aliases",
                    value="`%s`" % "`, `".join(cmd.aliases) if cmd.aliases else "None",
                )
            )

            await ctx.send(embed=embed)
        # Get a list of commands
        else:
            await ctx.send(embed=self.base_help_embed)

    @command(
        name="ping",
        description="Pong!",
        usage=">ping",
        aliases=(
            "latency",
            "pong",
        ),
    )
    async def ping(self, ctx) -> None:
        latency = str(round(self.bot.latency * 1000, 2)) + "ms"

        await ctx.send(embed=Embed(title="Pong :ping_pong: ", description=f"{latency}"))

    @command(
        name="invite",
        description="Invite the bot to your server.",
        usage=">invite",
        aliases=("inv",),
    )
    async def invite(self, ctx) -> None:
        await ctx.send(
            embed=Embed(
                description=":orange_heart: **[Click here to invite the bot.](%s)**"
                % INVITE_URL
            )
        )

    @command(
        name="vote",
        description="Vote for the bot.",
        usage=">vote",
        aliases=("v",),
    )
    async def vote(self, ctx) -> None:
        await ctx.send(
            embed=Embed(
                description=":orange_heart: **[Click here to vote for the bot.](%s)**"
                % VOTE_URL
            )
        )

    @command(
        name="support",
        description="Support the bot on GitHub.",
        usage=">support",
        aliases=(
            "supp",
            "sup",
        ),
    )
    async def support(self, ctx) -> None:
        await ctx.send(
            embed=Embed(
                description=":orange_heart: **[Click here to star & watch the bot on GitHub.](%s)**"
                % GITHUB_URL
            )
        )

    @command(
        name="usage",
        description="View command usage.",
        usage=">usage",
        hidden=True,
    )
    @is_owner()
    async def usage(self, ctx) -> None:
        # todo: doc these commands
        query = db.usage.find({}, {"_id": False})

        async for i in query:
            results = dict(i)
            sort = sorted(results, key=lambda x: results[x], reverse=True)
            usage = ["`>%s`: %d" % (x, results[x]) for x in sort]

            await ctx.send(embed=Embed(description="\n".join(usage)))

            return
