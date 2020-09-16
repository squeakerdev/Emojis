import re
import shutil
from asyncio import sleep

import discord
import pymongo as mg
import requests
from discord.ext import commands

# Setting up Database
MONGO_CLIENT = mg.MongoClient("mongodb://localhost:27017")
DATABASE = MONGO_CLIENT["Emojis"]
PREFIX_LIST = DATABASE["prefixes"]
SETTINGS = DATABASE["settings"]
APPROVAL_QUEUES = DATABASE["verification_queues"]

# stuff for replacing emojis
EMOJI_CONVERTER = commands.EmojiConverter()


class CustomCommandError(Exception):
    pass


# Colors used in the Bot
class Colours:
    base = discord.Color(16562199)
    success = discord.Color(3066993)
    fail = discord.Color(15742004)
    warn = discord.Color(16707936)


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

            # check if the server has approval queue enabled
            query = APPROVAL_QUEUES.find_one({"g": str(ctx.guild.id)},
                                             {"_id": 0,
                                              "queue_channel": 1,
                                              "queue": 1})

            # add the emoji to the approval queue
            try:
                if query["queue_channel"]:

                    # admins bypass the queue
                    if not ctx.message.author.guild_permissions.administrator:

                        # send a warning message
                        embed = discord.Embed(
                            colour=Colours.warn,
                            description=f"<:warningsmall:744570500919066706> **Hold your horses!** This server has an "
                                        f"emoji approval queue active. I'll upload your emoji once a moderator has"
                                        f" approved that it's a good emoji."
                        )

                        # send
                        await ctx.message.channel.send(embed=embed)

                        # add to queue
                        await add_to_emoji_queue(ctx.guild, [new_emoji], user=ctx.message.author)

                    # user is admin; bypass queue and post success msg
                    else:
                        # post the success message
                        if success_message:
                            embed = discord.Embed(
                                title=success_message,
                                colour=Colours.success,
                                description=f"`:{emoji_json['title']}:`\n\n"
                                            f"This server has an emoji approval queue, but you're an Administrator, "
                                            f"so you bypass it. Lucky you."
                            )

                            embed.set_thumbnail(url=emoji_json["image"])

                            # send
                            await ctx.message.channel.send(embed=embed)

            except:
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
async def on_guild_emojis_update(guild, before, after):
    """
    When an emoji is added to a server, delete it, and add it to the emoji queue if the server has one.

    :param guild: the guild in which an emoji was removed/added
    :param before: list of emojis before the event
    :param after: list of emojis after the event
    :return: N/A
    """

    # a list of new emojis (len should == 1)
    new_emojis = list(filter(lambda e: e not in before, after))

    if len(after) > len(before):
        await add_to_emoji_queue(guild, new_emojis)


async def add_to_emoji_queue(guild, new_emojis, user=None):

    # check if the server has approval queue enabled
    query = APPROVAL_QUEUES.find_one({"g": str(guild.id)},
                                     {"_id": 0,
                                      "queue_channel": 1,
                                      "queue": 1})

    try:
        if query["queue_channel"]:

            # get queue channel
            queue_channel = guild.get_channel(int(query["queue_channel"]))

            # remove emojis and queue them
            for new_emoji in new_emojis:
                url = str(new_emoji.url)  # url of image
                id_ = int(new_emoji.id)  # emoji id
                name = new_emoji.name  # emoji name
                uploaded_by = await guild.fetch_emoji(int(id_))  # uploaded by

                # get Member object of uploader so that permissions can be checked
                guild_user = guild.get_member(uploaded_by.user.id)

                # user is used if the emoji was installed through a command, to make it seem like the user who
                # invoked the command uploaded the emoji, rather than the bot
                #
                # this is done to prevent users from bypassing the queue by using commmands
                if user:
                    guild_user = user

                # if user is admin or user is the bot, bypass queue
                if not guild_user.guild_permissions.administrator and guild_user.id != 749301838859337799:
                    # otherwise, update DB with new addition to emoji queue
                    APPROVAL_QUEUES.update_one({"g": str(guild.id)},
                                               {
                                                   "$push": {
                                                       "queue": {
                                                           str(new_emoji.id): {"url": url,
                                                                               "id": id_,
                                                                               "name": name,
                                                                               "uploaded_by": str(uploaded_by.user)}
                                                       }}},
                                               upsert=True)

                    # delete the emoji while we hold it hostage
                    await new_emoji.delete(reason="Queueing this emoji for approval.")

                    embed = discord.Embed(
                        colour=Colours.base,
                        title="Emoji approval required",
                        description=f"{guild_user.name} wants to upload this emoji (`{name}`). Please "
                                    f"indicate via reaction whether or not you approve it."
                    )

                    embed.set_author(name=guild_user, icon_url=guild_user.avatar_url)
                    embed.set_image(url=url)

                    # send approval form to mod channel
                    approval_message = await queue_channel.send(embed=embed)

                    # add reacts
                    await approval_message.add_reaction("👍")
                    await approval_message.add_reaction("👎")

                    # reaction must:
                    # - not be by a bot
                    # - be either 👍 or 👎
                    # - be on the approval message
                    def check(payload):
                        return \
                            payload.message_id == approval_message.id \
                            and not payload.member.bot \
                            and payload.emoji.name in ["👍", "👎"]

                    reaction = await bot.wait_for("raw_reaction_add", check=check, timeout=None)

                    # emoji approved
                    if reaction.emoji.name == "👍":
                        installed_emoji = await install_emoji(guild, {"image": url, "title": name})

                        # update form with success message
                        await approval_message.edit(embed=discord.Embed(
                            colour=Colours.success,
                            title="Emoji approved",
                            description=f"{reaction.member} approved {installed_emoji}, uploaded "
                                        f"by {uploaded_by.user}."
                        ))
                    else:
                        # update form with deny message
                        await approval_message.edit(embed=discord.Embed(
                            colour=Colours.fail,
                            title="Emoji denied",
                            description=f"{reaction.member} denied {uploaded_by.user}'s emoji suggestion."
                        ))

    # emoji queue not enabled
    # bare except used to prevent errors filling up the console
    except:
        pass


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
        description=f"Hi, **{guild.name}**! I'm Emojis: a bot to easily manage your "
                    "server's emojis. My prefix is `>` (but you can change it with `>prefix`)!\n\n"
                    "**By default, I replace unparsed :emojis: that I find in the chat, so that you can use emojis "
                    "from other servers without Nitro.** If you have a similar bot, like NQN or Animated Emojis, "
                    "they might conflict. You can change this behaviour with `>replace off`.\n\n"
                    f"**Commands:** `{'`, `'.join(sorted([c.name for c in bot.commands]))}`",
        colour=Colours.base
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

    print(f"Serving {sum(guild.member_count for guild in bot.guilds)} users in {len(bot.guilds)} servers!")

    while 1:
        try:
            await sleep(20)
            await bot.change_presence(activity=discord.Game(name=f"ping for prefix | {len(bot.guilds)} servers"))
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
    startup_extensions = ["information", "settings", "emoji", "management"]

    for extension in startup_extensions:
        bot.load_extension(extension)

    with open("./data/token.txt", "r") as token:
        bot.run(token.readline())
