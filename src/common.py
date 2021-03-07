import discord
from typing import *


class Emojis:
    """ Emojis used in bot responses. """

    error = e = red = "<:redticksmall:736197216900874240>"
    success = s = green = "<:greenTick:769936017230266398>"
    neutral = n = gray = "<:greyTick:769937437899489301>"
    waiting = w = typing_ = "<a:typing:734095511916773417>"


class Colours:
    """ Colours used in bot responses. """

    error = r = red = discord.Color(15742004)
    success = g = green = discord.Color(3066993)
    neutral = n = normal = base = discord.Color(16562199)
    warn = y = yellow = discord.Color(16707936)


class ColouredEmbed(discord.Embed):
    """ A Discord Embed with a default colour. """

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        if "colour" not in kwargs and "color" not in kwargs:
            self.colour = Colours.base


# Replace the default Embed with the customised one
discord.Embed = ColouredEmbed
