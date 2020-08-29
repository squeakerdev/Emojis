import shutil
from asyncio import sleep
import discord
from discord.ext import commands
import pymongo as mg
import requests

mgclient = mg.MongoClient("mongodb://localhost:27017")
db = mgclient["Emojis"]
prefix_list = db["prefixes"]
settings = db["settings"]
queues = db["verification_queues"]


class CustomCommandError(Exception):
    pass


class States:
    OK = '[\033[94m-\033[0m]'
    SUCCESS = '[\033[92m+\033[0m]'
    WARNING = '[\033[93m?\033[0m]'
    FAIL = '[\033[91m!\033[0m]'


class Colours:
    base = discord.Color(7059952)
    success = discord.Color(3066993)
    fail = discord.Color(15742004)
    warn = discord.Color(16707936)


def get_prefix(client, message):
    prefix = prefix_list.find_one({"g": str(message.guild.id)}, {"_id": 0, "pr": 1})
    try:
        return prefix["pr"]
    except:
        return ">"


async def install_emoji(ctx, emoji_json, success_message: str = None):
    """
    Install an emoji.

    :param ctx: context of the target guild
    :param emoji_json: takes the format {"image": image_url, "title": emoji_name}
    :param success_message: the message to send to the channel upon emoji install. Defaults to None
    :return: the emoji installed
    """

    response = requests.get(emoji_json["image"], stream=True)

    if response.status_code == 200:
        with open(f"./emojis/{emoji_json['title']}.gif", "wb") as img:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, img)
    else:
        raise Exception(f"Bad status code uploading {emoji_json['title']} received: {response.status_code}")

    with open(f"./emojis/{emoji_json['title']}.gif", "rb") as image:
        if isinstance(ctx, discord.Guild):
            new_emoji = await ctx.create_custom_emoji(name=emoji_json['title'], image=image.read())
        else:
            new_emoji = await ctx.message.guild.create_custom_emoji(name=emoji_json['title'], image=image.read())

        if success_message:
            random_embed = discord.Embed(title=success_message)
            random_embed.colour = Colours.success
            random_embed.set_thumbnail(url=emoji_json["image"])
            random_embed.add_field(name="Emoji", value=f"`:{emoji_json['title']}:`")
            await ctx.message.channel.send(embed=random_embed)

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

    await bot.process_commands(message)


@bot.event
async def on_guild_emojis_update(guild, before, after):
    """
    When an emoji is added to a server, start emoji queue

    :param guild: the guild in which an emoji was removed/added
    :param before: list of emojis before the event
    :param after: list of emojis after the event
    :return: N/A
    """

    # an emoji was added
    if len(after) > len(before):
        # check if the server has approval queue enabled
        query = queues.find_one({"g": str(guild.id)},
                                {"_id": 0,
                                 "queue_channel": 1,
                                 "queue": 1})

        try:
            if query["queue_channel"]:
                # a list of new emojis (len should == 1)
                new_emojis = list(filter(lambda e: e not in before, after))

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

                    # if user is admin or user is the bot, bypass queue
                    if not guild_user.guild_permissions.administrator and guild_user.id != 749301838859337799:

                        # otherwise, update DB with new addition to emoji queue
                        queues.update_one({"g": str(guild.id)},
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
                            description=f"{uploaded_by.user.name} wants to upload this emoji (`{name}`). Please "
                                        f"indicate via reaction whether or not you approve it."
                        )

                        embed.set_author(name=uploaded_by.user, icon_url=uploaded_by.user.avatar_url)
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
                            print("Here")
                            # update form with deny message
                            await approval_message.edit(embed=discord.Embed(
                                colour=Colours.fail,
                                title="Emoji denied",
                                description=f"{reaction.member} denied {uploaded_by.user}'s emoji suggestion."
                            ))

        # emoji queue not enabled
        except KeyError:
            pass


@bot.event
async def on_ready():
    """
    Run setup stuff that only needs to happen once.
    """

    await bot.change_presence(activity=discord.Game(name=f"just updated!"))

    print(f"Serving {sum(guild.member_count for guild in bot.guilds)} users in {len(bot.guilds)} servers!")

    while 1:
        try:
            await sleep(20)
            await bot.change_presence(activity=discord.Game(name=f"ping for prefix | {len(bot.guilds)} servers"))
        except:
            continue


async def send_error(ctx, err, extra_info=None, full_error=None):
    """
    Send an error message to s specified channel; extra_info will add more detail.
    """

    error_embed = discord.Embed()
    error_embed.colour = Colours.fail
    error_embed.description = err

    if extra_info and isinstance(full_error, commands.CommandInvokeError) is False:
        error_embed.description = f"{err}\n\n**{extra_info['name']}:** `{extra_info['value']}`".replace("[BOT_PREFIX]",
                                                                                                        ctx.prefix)

    await ctx.send(embed=error_embed)


if __name__ == "__main__":
    startup_extensions = ["information", "settings"]

    for extension in startup_extensions:
        bot.load_extension(extension)

    with open("token.txt", "r") as token:
        bot.run(token.readline())
