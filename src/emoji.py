import discord.ext.commands as commands
import discord
import requests
import shutil
from src.common import *


async def install_emoji(ctx, emoji_json, success_message: str = None):
    # download the image
    download = requests.get(emoji_json["image"], stream=True)

    # image downloaded sucessfully
    if download.status_code == 200:
        with open(f"./emojis/{emoji_json['title']}.gif", "wb") as image:
            download.raw.decode_content = True
            shutil.copyfileobj(download.raw, image)

    else:
        raise Exception(
            f"Recieved bad status code uploading {emoji_json['title']}: {download.status_code}")

    with open(f"./emojis/{emoji_json['title']}.gif", "rb") as image:

        # install the emoji
        if isinstance(ctx, discord.Guild):
            new_emoji = await ctx.create_custom_emoji(name=emoji_json['title'], image=image.read())

        else:
            new_emoji = await ctx.message.guild.create_custom_emoji(name=emoji_json['title'], image=image.read())
            embed = discord.Embed(
                title=success_message,
                colour=Colours.success,
                description=f"`:{emoji_json['title']}:`"
            )

            embed.set_thumbnail(url=emoji_json["image"])

            # send the embed
            await ctx.message.channel.send(embed=embed)

        return new_emoji


def setup(bot):
    bot.add_cog(Emoji(bot))


class Emoji(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
