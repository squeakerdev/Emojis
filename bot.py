import asyncio
from os import listdir
from os.path import splitext
from re import search

from discord import Activity, ActivityType, Game, Message, Intents
from discord.ext.commands import (
    CommandNotFound,
    MissingRequiredArgument,
    CommandInvokeError,
    AutoShardedBot,
    EmojiConverter,
)

from src.common.common import *


async def get_prefix(client, message) -> str:
    """ Get the prefix for a guild. """
    # Private channel
    if not message.guild:
        return DEFAULT_PREFIX

    # Guild
    result = await db.settings.find_one({"id": message.guild.id}, {"prefix": 1})
    return result["prefix"] if result else DEFAULT_PREFIX


bot = AutoShardedBot(
    command_prefix=get_prefix,
    case_insensitive=True,
    owner_ids=[554275447710548018, 686941073792303157],
    intents=Intents.default(),
)


@bot.event
async def on_command_error(ctx, err) -> None:
    """
    Catch and handle errors thrown by the bot.

    :param ctx:
    :param err: The error thrown.
    """
    if isinstance(err, CommandNotFound):
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
            err = Exception(getattr(err, "original").text or str(err))  # noqa
        except AttributeError:
            pass

    # Attempt to simplify error message
    msg = str(getattr(err, "__cause__") or err)

    # Send the error to the user
    await send_error(ctx, msg)

    # For development purposes, so the error can be seen in console
    raise err


@bot.event
async def on_message(message) -> None:
    """ Post this guild's bot prefix if the user pings the bot. """

    # Post prefix
    if message.content.startswith("<@!749301838859337799>"):
        prefix = await get_prefix(bot, message)
        await message.channel.send(
            "%s This server's prefix is `%s`." % (message.author.mention, prefix)
        )

    # Continue processing message
    await bot.process_commands(message)

    # Replace unparsed :emojis:, NQN-style
    await replace_unparsed_emojis(message)


@bot.event
async def on_guild_join(guild) -> None:
    # Create the on-join Embed
    embed = Embed(
        title="Hi!",
        description=f"I'm Emojis: a bot to easily manage your "
        "server's emojis. My prefix is `>` (but you can change it with `>prefix`)!",
    )

    embed.add_field(
        name="Links",
        value="- [GitHub](https://github.com/passivity/emojis)\n"
        "- [Support server](https://discord.gg/wzG9Y8s)\n"
        "- [Vote (top.gg)](https://top.gg/bot/749301838859337799/vote)",
        inline=False,
    )

    # Send the Embed to the first channel the bot can type in
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(embed=embed)
            break

    # Create a webhook in each channel
    for channel in guild.text_channels:
        await channel.create_webhook(name="Emojis")


def run_once(func):
    """ Make sure a function only runs once. """
    # Used for on_ready since it may run multiple times, e.g. if disconnected from Discord

    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True

            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


@bot.event
async def on_ready() -> None:
    """
    Run setup stuff that only needs to happen once.
    """

    await bot.change_presence(activity=Game(name="just updated!"))
    await begin_updating_presence()


@run_once
async def begin_updating_presence():
    print("Serving {} guilds".format(len(bot.guilds)))

    while 1:
        try:
            await asyncio.sleep(20)
            await bot.change_presence(
                activity=Activity(
                    name=f"{len(bot.guilds)} servers | >help",
                    type=ActivityType.watching,
                )
            )

        except Exception as err:
            print("Failed to change presence:", err)


async def send_error(ctx, err: Union[str, Exception]) -> None:
    """
    Send an error to a specified channel.

    :param ctx:
    :param err: The error message to send
    """

    await ctx.send(
        embed=Embed(colour=Colours.error, description=f"{Emojis.error} {err}")
    )


async def replace_unparsed_emojis(message: Message):
    """ Replace unparsed ':emojis:' in a message, to simulate Discord Nitro. Sends the modified message on a Webhook
    that looks like the user. """
    has_updated = False

    if not message.author.bot:
        # Check for :emojis:
        match = bool(search(r":[a-zA-Z0-9_-]+:", message.content))

        if match:
            ctx = await bot.get_context(message)
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
                    except BadArgument as e:
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
    # Remove the default help command so a better one can be added
    bot.remove_command("help")

    # Load cogs
    # Ignores files starting with "_", like __init__.py
    for cog in listdir("./src/exts/"):
        if not cog.startswith("_"):
            file_name, file_extension = splitext(cog)
            bot.load_extension("src.exts.%s" % file_name)

    # Code written after this block may not run
    with open("./data/token.txt", "r") as token:
        bot.run(token.readline())
