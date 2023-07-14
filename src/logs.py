#logs.py

import logging, inspect
from datetime import datetime
import traceback
from src.files import Directory
from src.database import Config
from os import path
from interactions import (
        EMBED_MAX_DESC_LENGTH,
        Client,
        EmbedAuthor,
        SlashContext,
        Embed,
        GuildText,
        Member,
        Attachment,
        Role
    )
from interactions.api.events.internal import CommandError
from lookups.colors import Color

# Takes slash command context and returns the command used formatted nicely
def get_slash_command(ctx: SlashContext):
    command = "/" + ctx._command_name

    for arg in ctx.kwargs:
        option = ctx.kwargs[arg]

        # Option is channel
        if isinstance(option, GuildText):
            option = option.name

        # Option is member
        if isinstance(option, Member):
            option = option.username

        # Option is role
        if isinstance(option, Role):
            option = f"@{option.name}"

        # Option is attachment
        if isinstance(option, Attachment):
            option = f"[{option.filename}]({option.url})"

        command += f" {arg}:{option}"

    return command

class DiscordLogger:
    @classmethod
    async def log(self, bot: Client, ctx: SlashContext, description: str = ""):
        logging_channel_id = Config.get_config_parameter(name="logging", key="channel_id")
        logging_channel = await bot.fetch_channel(logging_channel_id)

        embed = Embed(
            author=EmbedAuthor(name=ctx.author.username, icon_url=ctx.author.avatar.url),
            description=f"User {ctx.author.mention} used a slash command in {ctx.channel.mention}.",
            color=Color.WHITE
        )

        embed.add_field(name="Command", value=f"`{get_slash_command(ctx)}`")

        if description:
            embed.add_field(name="Description", value=description)

        await logging_channel.send(embed=embed)

    @classmethod
    async def log_raw(self, bot: Client, description: str = ""):
        logging_channel_id = Config.get_config_parameter(name="logging", key="channel_id")
        logging_channel = await bot.fetch_channel(logging_channel_id)

        embed = Embed(
            author=EmbedAuthor(name=bot.user.username, icon_url=bot.user.avatar.url),
            description=description,
            color=Color.WHITE
        )

        await logging_channel.send(embed=embed)

    @classmethod
    async def log_error(self, bot: Client, error: CommandError):
        logging_channel_id = Config.get_config_parameter(name="logging", key="channel_id")
        logging_channel = await bot.fetch_channel(logging_channel_id)

        out = "".join(traceback.format_exception(error.error))

        embed = Embed(
            title=f"Error: {type(error.error).__name__}",
            author=EmbedAuthor(name=bot.user.username, icon_url=bot.user.avatar.url),
            description=f"```\n{out[:EMBED_MAX_DESC_LENGTH - 8]}```",
            color=Color.RED
        )

        embed.add_field(name="Details", value=f"Error occurred in slash command used by {error.ctx.author.mention}: ```{get_slash_command(error.ctx)}```")

        await logging_channel.send(embed=embed)

### Most of the stuff below is based on 'logutil' from the old interactions.py boilerplate ###

def get_logger(name):
    '''Gets a logger'''

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())
    logger.addHandler(stream_handler)

    return logger

def init_logger(name = ""):
    '''Creates a new logger'''
    
    if not name:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = path.basename(module.__file__)[:-3]

    logger = logging.Logger(name)

    # Create logs directory if it doesn't exist yet
    logs_directory = Directory("./logs/").create()

    # Setup file logging, all loggers to same file using custom file formatter
    file_handler = logging.FileHandler(f'./logs/{datetime.utcnow().strftime("%Y-%m-%d")}.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(CustomFileFormatter())
    logger.addHandler(file_handler)

    # Setup custom formatter for console logging
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(CustomFormatter())
    logger.addHandler(stream_handler)

    # logger.info(f"Initialized '{name}' logger")

    return logger

class CustomFormatter(logging.Formatter):
    """Custom formatter class"""
    grey = "\x1b[38;1m"
    green = "\x1b[42;1m"
    yellow = "\x1b[43;1m"
    red = "\x1b[41;1m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: green + f"{reset}[%(asctime)s]{green}[%(levelname)-7s][%(name)-14s]{reset}[{red}%(lineno)4s{reset}] %(message)s" + reset,
        logging.INFO: grey + f"{reset}[%(asctime)s]{grey}[%(levelname)-7s][%(name)-14s]{reset}[{red}%(lineno)4s{reset}] %(message)s" + reset,
        logging.WARNING: yellow + f"[%(asctime)s][%(levelname)-7s][%(name)-14s][{red}%(lineno)4s{reset}{yellow}] %(message)s" + reset,
        logging.ERROR: red + "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s" + reset,
        logging.CRITICAL: bold_red + "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%I:%M.%S%p")
        return formatter.format(record)

class CustomFileFormatter(logging.Formatter):
    """Custom file formatter class"""

    FORMATS = {
        logging.DEBUG: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.INFO: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.WARNING: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.ERROR: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.CRITICAL: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%I:%M.%S%p")
        return formatter.format(record)
    
if __name__ == "__main__":
    test_logger = init_logger("test")
    test_logger.info("some info")
    test_logger.debug("some debug")
    test_logger.warning("some warning")
    test_logger.error("some error")