from random import choice

import discord
import pymongo as mg
from discord.ext import commands
from discord.ext.commands import has_permissions

from bot import Colours, install_emoji
from bot import CustomCommandError

mgclient = mg.MongoClient("mongodb://localhost:27017")
db = mgclient["Emojis"]
prefix_list = db["prefixes"]
settings = db["settings"]
queues = db["verification_queues"]


def setup(bot):
    bot.add_cog(Emoji(bot))


class Emoji(commands.Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="jumbo",
                      description="View an emoji in full size.",
                      usage=">jumbo :emoji:",
                      aliases=["j", "big", "size", "sizeup"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(manage_emojis=True)
    async def jumbo(self, ctx, emojis: commands.Greedy[discord.PartialEmoji]):
        """
        Return an emoji's full-size image.

        :param ctx: context
        :param emojis: an emoji or list of emojis to get the image for
        :return: N/A
        """

        # no emojis provided
        if len(emojis) == 0:
            raise CustomCommandError("You need to input at least one custom emoji.")
        elif len(emojis) > 3:
            raise CustomCommandError("This command is limited to 3 emojis.")

        # embed
        embed = discord.Embed(colour=Colours.success)

        for emoji in emojis:
            # add image
            embed.set_image(url=emoji.url)

            # send embed
            await ctx.message.channel.send(embed=embed)

    @commands.command(name="random",
                      description="Add a random emoji to your server.",
                      usage=">random` or `>random [name for emoji]",
                      aliases=["rand", "randomemoji"],
                      pass_context=True)
    @has_permissions(manage_emojis=True)
    async def random(self, ctx, name_for_emoji=None):
        """
        Install a random emoji from the bot's cache.

        :param ctx: context
        :param name_for_emoji: (optional) a custom name for the emoji
        :return: N/A
        """

        # pick random emoji from cache of all emojis
        emoji = choice(self.bot.emojis)
        emoji_to_upload = {"title": emoji.name, "image": str(emoji.url)}

        # install
        if name_for_emoji is not None:
            emoji_to_upload["title"] = name_for_emoji

        await install_emoji(ctx, emoji_to_upload, success_message="Random emoji added")

    @commands.command(name="info",
                      description="Get information on an emoji.",
                      usage=">info [emoji]",
                      aliases=["?", "details", "d"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def get_emoji_info(self, ctx, emoji: discord.Emoji):
        """
        Get information on an emoji from the current server.

        :param ctx: context
        :param emoji: the emoji to get information on. must be a custom emoji from the current server
        :return: N/A
        """

        # required to get user who made emoji
        try:
            emoji = await ctx.guild.fetch_emoji(emoji.id)
        except Exception:
            raise CustomCommandError(f"I can't find that emoji. Make sure it's from **this** server "
                                     f"({ctx.guild.name}).")

        # setup
        emoji_details_embed = discord.Embed(title=emoji.name, colour=Colours.base)
        emoji_details_embed.set_thumbnail(url=emoji.url)

        # fields
        emoji_details_embed.add_field(name="ID", value=emoji.id, inline=True)
        emoji_details_embed.add_field(name="Usage", value=f"`:{emoji.name}:`", inline=True)
        emoji_details_embed.add_field(name="Created at", value=emoji.created_at, inline=True)
        emoji_details_embed.add_field(name="Created by", value=emoji.user, inline=True)
        emoji_details_embed.add_field(name="URL", value=f"[Link]({emoji.url})", inline=True)
        emoji_details_embed.add_field(name="Animated", value=emoji.animated, inline=True)

        # send
        await ctx.channel.send(embed=emoji_details_embed)
        
        
        @commands.command(name="replace",
                      description="Use emojis from other servers for free. **Emojis must be in the server that you"
                                  " want to use emojis from.**",
                      usage=">replace [:emoji from another server:]",
                      aliases=["r", "nqn", "nitro", "nitroify", "free"],
                      pass_context=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def convert(self, ctx, *msg):

        o_msg = list(msg)  # original message
        msg = list(msg)

        count = 0

        # find :unparsed emojis: in message
        for word in msg:
            word_results = re.search(r":(.*?):", word)
            if word_results is None:
                msg[count] = "-"

            count += 1

        count = 0
        # try to replace emojis with real emojis
        for word in msg:
            if word != "-":  # non-emoji words are replaced with "-"
                try:
                    word = word[1:-1]  # omit colons
                    emoji = await conv.convert(ctx=ctx, argument=word)
                    msg[count] = emoji
                    if emoji.animated:
                        msg[count] = f"<a:{msg[count].name}:{msg[count].id}>"
                    else:
                        msg[count] = f"<:{msg[count].name}:{msg[count].id}>"
                except:
                    msg[count] = o_msg[count]
            else:
                msg[count] = o_msg[count]
            count += 1

        # store avatar
        with open(f'./emojis/{ctx.message.author.id}.jpg', 'wb') as av:
            av.write(requests.get(ctx.message.author.avatar_url).content)

        # set up webhook - could be optimised by setting up the webhook on server join and using utils.get to find it
        with open(f'./emojis/{ctx.message.author.id}.jpg', 'rb') as av:
            try:
                wh = await ctx.message.channel.create_webhook(name=ctx.message.author.display_name,
                                                              avatar=av.read(),
                                                              reason=f"Replacing emojis from {ctx.message.author}")
            except:
                raise CustomCommandError("Hey, I need an extra permission for that. Ask a mod to give my role (@Emojis)"
                                         " the Manage Webhooks permission!")

        # send on webhook
        await wh.send(" ".join(msg))
        try:
            await ctx.message.delete()
        except:
            raise CustomCommandError("Hey, I need an extra permission for that. Ask a mod to give my role (@Emojis)"
                                     " the Manage Messages permission!")

        # del webhook
        await wh.delete()

        # del file
        remove(f'./emojis/{ctx.message.author.id}.jpg')
