import re
import shutil
from asyncio import sleep

import discord
import requests

from src.common import *
from src.exceptions import *


async def replace_unparsed_emojis(message: discord.Message):
    """
    Replace unparsed emojis in the user's message with emojis from other servers.

    :param message: the message in question
    :return: the message sent (if no message was sent, returns the original message)
    """

    query = SETTINGS.find_one({"g": str(message.guild.id)},
                              {"_id": 0,
                               "replace_emojis": 1})

    if not query or query["replace_emojis"] is True:

        # messages from bots aren't replaced
        if not message.author.bot and not str(message.author).endswith("#0000"):

            # split message into list of words
            message_list = message.content.split(" ")

            # the list that will contain the message with emojis replaced
            message_with_replaced_emojis = []

            # indicates whether anything needs to be sent on the webhook
            emojis_found = False

            # replace emojis in each word
            for word in message_list:

                # regex to find :emojis:
                if re.search(r":(.*?):", word):

                    # get context from the message so that it can be used in EmojiConverter
                    ctx = await bot.get_context(message)

                    # convert the emoji
                    try:
                        emoji = await EMOJI_CONVERTER.convert(ctx=ctx, argument=word.replace(":", ""))
                        message_with_replaced_emojis.append(str(emoji))

                        # indicate that emojis were replaced and the message needs to be sent on webhook
                        emojis_found = True

                    # no emoji found
                    except commands.BadArgument:
                        message_with_replaced_emojis.append(word)

                    # miscellaneous errors
                    except Exception as err:
                        raise CustomCommandError(err)

                # no unparsed emoji found; just add the word
                else:
                    message_with_replaced_emojis.append(word)

            # if emojis were replaced, send on webhook
            if emojis_found:
                channel_webhooks = await message.channel.webhooks()

                # find the webhook created on server join
                webhook = discord.utils.get(channel_webhooks, name="Emojis")

                # no webhook found; make one instead
                if not webhook:
                    webhook = await message.channel.create_webhook(name="Emojis")

                # delete message
                await message.delete()

                print("Processing message by", str(message.author), f"({message.content})")

                # send replaced message on webhook
                message = await webhook.send(" ".join(message_with_replaced_emojis),
                                             username=message.author.display_name,
                                             avatar_url=message.author.avatar_url)

    return message


def get_prefix(client, message):
    """
    Get the prefix for a specified server.

    :param client: the bot
    :param message: the message object that needs checking (comes from on_message)
    :return: the server's custom prefix (str)
    """
    try:
        guild = message.guild
    except AttributeError:
        guild = message

    # query database
    prefix = PREFIX_LIST.find_one({"g": str(guild.id)}, {"_id": 0, "pr": 1})

    # return prefix
    try:
        return prefix["pr"]
    except KeyError:
        return ">"
    except TypeError:
        return ">"


async def install_emoji(ctx, emoji_json, success_message: str = None, uploaded_by: discord.Member = None):
    """
    Install an emoji.

    :param ctx: context of the target guild
    :param emoji_json: takes the format {"image": image_url, "title": emoji_name}
    :param success_message: the message to send to the channel upon emoji install. Defaults to None
    :param uploaded_by: the person who ran the command that uploaded this emoji
    :return: the emoji installed (discord.Emoji)
    """

    # download image data
    response = requests.get(emoji_json["image"], stream=True)

    # image downloaded successfully
    if response.status_code == 200:

        # save image to file
        with open(f"./emojis/{emoji_json['title']}.gif", "wb") as img:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, img)

    # failed to download
    else:
        raise Exception(f"Bad status code uploading {emoji_json['title']} received: {response.status_code}")

    with open(f"./emojis/{emoji_json['title']}.gif", "rb") as image:

        # install directly to guild
        if isinstance(ctx, discord.Guild):
            new_emoji = await ctx.create_custom_emoji(name=emoji_json['title'], image=image.read())

        # get guild from context, then install
        else:
            new_emoji = await ctx.message.guild.create_custom_emoji(name=emoji_json['title'], image=image.read())

            # server doesn't have queue enabled; post the success message
            if success_message:
                embed = discord.Embed(
                    title=success_message,
                    colour=Colours.success,
                    description=f"`:{emoji_json['title']}:`"
                )

                embed.set_thumbnail(url=emoji_json["image"])

                # send
                await ctx.message.channel.send(embed=embed)

        return new_emoji


bot = commands.AutoShardedBot(command_prefix=get_prefix, case_insensitive=True, owner_ids=[554275447710548018])


@bot.event
async def on_message(message):
    """
    Check if the user pinged the bot; if they did, tell them the bot's prefix.
    """

    if message.content.startswith("<@!749301838859337799>"):
        prefix = get_prefix(bot, message)
        await message.channel.send(f"{message.author.mention}, this server's prefix is `{prefix}`. Try `{prefix}help`"
                                   f" to get started.")

    message = await replace_unparsed_emojis(message)

    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    """
    Send a message on guild join, then create a webhook to be used in the replace command.

    :param guild: the guild that was joined
    :return: N/A
    """

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

    prefix = get_prefix(bot, guild)

    bot_user = await guild.fetch_member(749301838859337799)
    await bot_user.edit(nick=f"[{prefix}] Emojis")


@bot.event
async def on_ready():
    """
    Run setup stuff that only needs to happen once.
    """

    await bot.change_presence(activity=discord.Game(name="just updated!"))

    while 1:
        try:
            await sleep(20)
            await bot.change_presence(activity=discord.Activity(name=f"{len(bot.guilds)} servers | >help",
                                                                type=discord.ActivityType.watching))

            requests.post(f"https://discord.bots.gg/api/v1/bots/749301838859337799/stats",
                          headers={"Authorization": BOTS_GG_TOKEN},
                          data={"guildCount": len(bot.guilds),
                                "shardCount": len(bot.latencies)})

        except Exception as err:
            print("Failed to change presence:", err)


async def send_error(ctx, err, extra_info=None, full_error=None):
    """
    Send an error message to a specified channel.

    :param ctx: context
    :param err: the error string
    :param extra_info: any extra info that the user might want to know
    :param full_error: the full error
    :return: N/A
    """

    error_embed = discord.Embed()
    error_embed.colour = Colours.fail
    error_embed.description = err

    if extra_info and isinstance(full_error, commands.CommandInvokeError) is False:
        error_embed.description = f"{err}\n\n**{extra_info['name']}:** `{extra_info['value']}`".replace("[BOT_PREFIX]",
                                                                                                        ctx.prefix)

    await ctx.send(embed=error_embed)


if __name__ == "__main__":
    startup_extensions = [
        "information",
        "settings",
        "emoji",
        "management"
    ]

    for extension in startup_extensions:
        bot.load_extension(f"src.{extension}")

    with open("./data/token.txt", "r") as token:
        bot.run(token.readline())
