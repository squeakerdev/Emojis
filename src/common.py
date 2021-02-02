import pymongo as mg
from typing import Union, Any
from discord import Color, TextChannel
from discord.ext import commands
import logging

# Database
MONGO_CLIENT: mg.MongoClient = mg.MongoClient("mongodb://localhost:27017")
DATABASE: Any = MONGO_CLIENT["Emojis"]
PREFIX_LIST: Any = DATABASE["prefixes"]
SETTINGS: Any = DATABASE["settings"]
APPROVAL_QUEUES: Any = DATABASE["verification_queues"]
COMMAND_USAGE: Any = DATABASE["command_usage"]
VOTES: Any = DATABASE["votes"]

# API stuff
BOTS_GG_TOKEN: str = ""


# Colors used in the Bot
class Colours:
    base: Color = Color(16562199)
    success: Color = Color(3066993)
    fail: Color = Color(15742004)
    warn: Color = Color(16707936)


# Custom logging class (can be modified to send Discord alerts etc.)
class DiscordLogger(logging.Logger):
    channel: TextChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log(self, *args, **kwargs):
        # TODO: add Discord alerts
        super().log(*args, **kwargs)


# Logger
LOGGER = DiscordLogger(__name__)

# Converters
EMOJI_CONVERTER = commands.EmojiConverter()
PARTIAL_EMOJI_CONVERTER = commands.PartialEmojiConverter()
