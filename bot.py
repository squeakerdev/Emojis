import asyncio
import logging
from os import listdir
from os.path import splitext
from re import search

from discord import (
    Activity,
    ActivityType,
    Message,
    Intents,
    AllowedMentions,
    HTTPException,
)
from discord.ext.commands import (
    CommandNotFound,
    MissingRequiredArgument,
    CommandInvokeError,
    AutoShardedBot,
    EmojiConverter,
    BucketType,
    CooldownMapping,
)

from src.common.common import *

log = logging.Logger(__name__)

GLOBAL_COOLDOWN = (1.0, 5.0)  # (1.0, 5.0) = 1 command per 5 seconds
WELCOME_MSG = (
    "Thanks for inviting Emojis. My prefix is `>`.\n\n"
    "%s **Important: [Read about getting started](https://github.com/passivity/emojis/blob/master/README.md)**."
    % CustomEmojis.warning
)


class CustomContext(Context):
    """ A custom Context class with additional methods. """

    async def send_error(self, err: Union[str, Exception]) -> None:
        """ Send an error Embed to a specified channel. """

        await self.send(
            embed=Embed(colour=Colours.error, description=f"{CustomEmojis.error} {err}")
        )

    async def send_success(self, string):
        """ Send a success Embed to a specified channel. """

        await self.send(
            embed=Embed(
                colour=Colours.success,
                description="%s %s" % (CustomEmojis.success, string),
            )
        )


class Emojis(AutoShardedBot):
    """ A custom AutoShardedBot class with overridden methods."""

    def __init__(self):
        self.cooldown = CooldownMapping.from_cooldown(*GLOBAL_COOLDOWN, BucketType.user)
        self.command_usage = {}

        # Make sure the bot can't be abused to mass ping
        allowed_mentions = AllowedMentions(roles=False, everyone=False, users=True)

        # Minimum required
        intents = Intents(guilds=True, emojis=True, messages=True, reactions=True)

        super().__init__(
            command_prefix=">",
            description="An emoji management bot.",
            pm_help=None,
            fetch_offline_members=False,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
        )

        # Update presence continuously
        self.presence_updater = self.loop.create_task(self._bg_update_presence())
        self.usage_updater = self.loop.create_task(self._bg_update_usage())

    async def get_context(self, message, *, cls=CustomContext):
        """ Use CustomContext instead of Context. """
        return await super().get_context(message, cls=cls)

    async def on_message(self, message) -> None:
        # Process message
        await self.process_commands(message)

        # Replace unparsed :emojis:, NQN-style
        await self.replace_unparsed_emojis(message)

    async def on_command_error(self, ctx, err) -> None:
        """
        Catch and handle errors thrown by the bot.

        :param ctx:
        :param err: The error thrown.
        """
        if isinstance(err, CheckFailure):
            return
        elif isinstance(err, CommandNotFound):
            return  # Ignore
        elif isinstance(err, MissingRequiredArgument):
            # Make missing argument errors clearer
            err = Exception(
                "You're missing an argument (`%s`). Type `>help %s` for more info."
                % (err.param.name, ctx.command)
            )
        elif isinstance(err, CommandInvokeError):
            # Try to simplify HTTP errors
            try:
                err = Exception(getattr(err, "original").text or str(err))
            except AttributeError:
                pass

        # Attempt to simplify error message
        msg = str(getattr(err, "__cause__") or err)

        # Send the error to the user
        await ctx.send_error(msg)

        # For development purposes, so the error can be seen in console
        # raise err

    async def on_command_completion(self, ctx):
        cmd = ctx.command.name.lower()

        self.command_usage[cmd] = self.command_usage.get(cmd, 0) + 1

    async def on_guild_join(self, guild) -> None:  # noqa
        """ Send a welcome message, and create the Emojis webhook in each channel. """

        # Find the first channel the bot can type in and send the welcome message
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(embed=Embed(description=WELCOME_MSG))
                break

        for channel in guild.text_channels:
            await channel.create_webook(name="Emojis")

    async def on_ready(self) -> None:  # noqa
        print("Bot ready!")

    async def _bg_update_presence(self, delay: int = 20) -> None:
        """ Update the bot's status continuously. """

        await self.wait_until_ready()

        while not self.is_closed():  # Loop forever
            try:
                await self.change_presence(
                    activity=Activity(
                        name=f"{len(self.guilds)} servers | >help",
                        type=ActivityType.watching,
                    )
                )
            except HTTPException:
                pass

            await asyncio.sleep(delay)

    async def _bg_update_usage(self, delay: int = 900):
        """ Update the bot's usage stats in MongoDB. """

        await self.wait_until_ready()

        while not self.is_closed():
            for cmd, usage in self.command_usage.items():
                await db.usage.update_one(
                    {}, {"$inc": {cmd.lower(): usage}}, upsert=True
                )

            await asyncio.sleep(delay)

    async def replace_unparsed_emojis(self, message: Message):
        """
        Replace unparsed ':emojis:' in a message, to simulate Discord Nitro.
        Sends the modified message on a Webhook that looks like the user.
        """
        has_updated = False

        if not message.author.bot:
            # Check for :emojis:
            match = bool(search(r":[a-zA-Z0-9_-]+:", message.content))

            if match:
                ctx = await self.get_context(message)
                message_split = message.content.split()

                # Loop through every word and try to make it an emoji
                for i in range(len(message_split)):
                    word = message_split[i]

                    # Matches unparsed emojis
                    if search(r":[a-zA-Z0-9_-]+:", word):
                        try:
                            # Convert to Emoji
                            found_emoji = await EmojiConverter().convert(
                                ctx, word.replace(":", "")
                            )

                            message_split[i] = str(found_emoji)
                            has_updated = True
                        except BadArgument:
                            pass

                if has_updated:
                    # Find the bot's Webhook and send the message on it
                    webhook = await get_emojis_webhook(ctx)

                    await webhook.send(
                        " ".join(message_split),
                        username=message.author.display_name,
                        avatar_url=message.author.avatar_url,
                    )

                    await message.delete()


if __name__ == "__main__":
    bot = Emojis()

    # Remove the default help command so a better one can be added
    bot.remove_command("help")

    # Load cogs
    # Ignores files starting with "_", like __init__.py
    for cog in listdir("./src/exts/"):
        if not cog.startswith("_"):
            file_name, file_extension = splitext(cog)
            bot.load_extension("src.exts.%s" % file_name)

    # Reload the Misc extension to update the help command
    bot.reload_extension("src.exts.misc")

    # Code written after this block may not run
    with open("./data/token.txt", "r") as token:
        bot.run(token.readline())
