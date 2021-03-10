import asyncio
import os
from os import listdir
from os.path import splitext
from zipfile import ZipFile

from discord import Activity, ActivityType, Game, HTTPException
from discord.ext.commands import (
    CommandNotFound,
    MissingRequiredArgument,
    CommandInvokeError,
    AutoShardedBot,
)

from src.common.common import *


async def get_prefix(client, message) -> str:
    """ Get the prefix for a guild. """
    result = await db.settings.find_one({"id": message.guild.id}, {"prefix": 1})
    return result["prefix"] if result else ">"


bot = AutoShardedBot(
    command_prefix=get_prefix,
    case_insensitive=True,
    owner_ids=[554275447710548018, 686941073792303157],
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


@bot.event
async def on_ready() -> None:
    """
    Run setup stuff that only needs to happen once.
    """

    await bot.change_presence(activity=Game(name="just updated!"))

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
