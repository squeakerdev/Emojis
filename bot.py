from sqlite3.dbapi2 import sqlite_version
from typing import Counter
import discord
from discord import colour
import discord.ext.commands as commands
import requests
import time
import asyncio
import aiosqlite as sqlite


async def init_db():
    db = await sqlite.connect("bot.db")

    try:
        await db.execute("CREATE TABLE prefixes (guild_id INTEGER, prefix STRING)")
    except sqlite.OperationalError as err:
        print("Database existing, using that one.")
    await db.close()


async def get_prefix(client, message):
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
    command_prefix=get_prefix, case_insensitive=True, owner_ids=[686941073792303157686941073792303157])

bot.loop.create_task(init_db())

with open("./data/botsggtoken.txt") as token:
    BOTS_GG_TOKEN = token.readline()


# Colors used in the Bot
class Colours:
    base: discord.Color = discord.Color(16562199)
    success: discord.Color = discord.Color(3066993)
    fail: discord.Color = discord.Color(15742004)
    warn: discord.Color = discord.Color(16707936)


@bot.event
async def on_message(message):
    if message.content.startswith("<@!749301838859337799>"):
        prefix = get_prefix(bot, message)
        await message.channel.send(f"{message.author.mention}, this server's prefix is `{prefix}`. Try `{prefix}help`"
                                   f" to get started.")

    # message = await replace_unparsed_emojis(message)

    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    # create the join embed
    embed = discord.Embed(
        title="Hi!",
        description=f"👋 Hi, **{guild.name}**! I'm Emojis: a bot to easily manage your "
                    "server's emojis. My prefix is `>` (but you can change it with `>prefix`)!\n\n"

                    "<:warningsmall:744570500919066706> By default, I replace unparsed :emojis: that I find in the "
                    "chat, so that you can use emojis from other servers without Nitro. If you have a similar bot, "
                    "like NQN or Animated Emojis, they might conflict. You can change this behaviour with "
                    "`>replace off`.",
        colour=Colours.base
    )

    embed.add_field(
        name="Links",
        value="[GitHub](https://github.com/passivity/emojis)\n"
              "[Support server](https://discord.gg/wzG9Y8s)\n"
              "[Vote (top.gg)](https://top.gg/bot/749301838859337799/vote)",
        inline=False
    )

    # send to the first channel the bot can type in
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(embed=embed)
            break

    # create a webhook in every text channel
    for channel in guild.text_channels:
        await channel.create_webhook(name="Emojis")

    prefix = ">"

    # Using another bot for testing purposes
    bot_user = await guild.fetch_member(811263136551534633)
    # bot_user = await guild.fetch_member(749301838859337799)
    await bot_user.edit(nick=f"[{prefix}] Emojis")


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
            await bot.change_presence(activity=discord.Activity(name=f"{len(bot.guilds)} servers | >help",
                                                                type=discord.ActivityType.watching))

            requests.post(f"https://discord.bots.gg/api/v1/bots/749301838859337799/stats",
                          headers={"Authorization": BOTS_GG_TOKEN},
                          data={"guildCount": len(bot.guilds),
                                "shardCount": len(bot.latencies)})

        except Exception as err:
            print("Failed to change presence:", err)


@bot.command(name="ping")
async def ping(ctx):
    current_shard = (ctx.guild.id >> 22) % bot.shard_count
    latency = str(round(bot.latencies[current_shard][1], 2)) + "ms"
    embed = discord.Embed(title="Pong :ping_pong: ",
                          description=f"{latency}", colour=Colours.base)
    await ctx.send(embed=embed)


async def send_error(ctx, err, extra_info=None, full_error=None):
    error_embed = discord.Embed()
    error_embed.colour = Colours.fail
    error_embed.description = err

    if not (extra_info and isinstance(full_error, commands.CommandInvokeError)):
        error_embed.description = f"{err}\n\n**{extra_info['name']}:** `{extra_info['value']}`".replace("[BOT_PREFIX]",
                                                                                                        ctx.prefix)

    await ctx.send(embed=error_embed)

if __name__ == "__main__":
    # Remove the default help command so a better one can be added
    bot.remove_command("help")

    # Load cogs -- new cogs must be added manually to this list
    # Always load help.py last so that the command list is up-tp-date
    for cog in ("src.emoji", "src.help"):
        bot.load_extension(cog)

    with open("./data/token.txt", "r") as token:
        bot.run(token.readline())
