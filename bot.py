import asyncio
import re

import aiosqlite as sqlite
import discord.ext.commands as commands

from src.common import *


async def init_db() -> None:
    db = await sqlite.connect("bot.db")

    try:
        await db.execute("CREATE TABLE prefixes (guild_id INTEGER, prefix STRING)")
    except sqlite.OperationalError as err:
        print("Database existing, using that one.")
    await db.close()


async def get_prefix(client, message) -> str:
    try:
        guild = message.guild
    except AttributeError:
        guild = message
    try:
        db = await sqlite.connect("bot.db")
        await db.execute("SELECT prefix FROM prefixes WHERE guild_id=?", guild.id)
        result = await db.fetchall()
        await db.close()
    except:
        return ">"


bot = commands.AutoShardedBot(
    command_prefix=get_prefix,
    case_insensitive=True,
    owner_ids=[686941073792303157686941073792303157],
)

bot.loop.create_task(init_db())


@bot.event
async def on_command_error(ctx, err) -> None:
    """
    Catch and handle errors thrown by the bot.

    :param ctx:
    :param err: The error thrown.
    """
    # Attempt to simplify error message
    msg = str(getattr(err, "__cause__") or err)

    # Simplify HTTP errors
    # Example:
    #    "400 Bad Request (error code: 30008): Maximum number of emojis reached (50)"
    #    becomes:
    #    "Maximum number of emojis reached (50)"
    match = re.search(r"error code: (\d*)\): ", msg)
    if match:
        msg = msg[match.span()[1] :]

    # Send the error to the user
    await send_error(ctx, msg)

    # For development purposes, so the error can be seen in console
    # This shows the full error, not the simplified version
    raise err


@bot.event
async def on_message(message):
    if message.content.startswith("<@!749301838859337799>"):
        prefix = get_prefix(bot, message)
        await message.channel.send(
            f"{message.author.mention}, this server's prefix is `{prefix}`. Try `{prefix}help`"
            f" to get started."
        )

    # message = await replace_unparsed_emojis(message)

    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    # Create the on-join Embed
    embed = discord.Embed(
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
async def on_ready():
    """
    Run setup stuff that only needs to happen once.
    """

    await bot.change_presence(activity=discord.Game(name="just updated!"))

    print("Serving {} guilds".format(len(bot.guilds)))

    while 1:
        try:
            await asyncio.sleep(20)
            await bot.change_presence(
                activity=discord.Activity(
                    name=f"{len(bot.guilds)} servers | >help",
                    type=discord.ActivityType.watching,
                )
            )

        except Exception as err:
            print("Failed to change presence:", err)


@bot.command(name="ping")
async def ping(ctx):
    current_shard = (ctx.guild.id >> 22) % bot.shard_count
    latency = str(round(bot.latencies[current_shard][1], 2)) + "ms"
    embed = discord.Embed(title="Pong :ping_pong: ", description=f"{latency}")
    await ctx.send(embed=embed)


async def send_error(ctx, err: Union[str, Exception]):
    """
    Send an error to a specified channel.

    :param ctx:
    :param err: The error message to send
    """

    await ctx.send(
        embed=discord.Embed(colour=Colours.error, description=f"{Emojis.error} {err}")
    )


if __name__ == "__main__":
    # Remove the default help command so a better one can be added
    bot.remove_command("help")

    # Load cogs -- new cogs must be added manually to this list
    # Always load help.py last so that the command list is up-tp-date
    for cog in ("src.emoji", "src.help"):
        bot.load_extension(cog)

    # Code written after this block may not run
    with open("./data/token.txt", "r") as token:
        bot.run(token.readline())
