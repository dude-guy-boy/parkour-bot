# autosync.py

from interactions import (
    Client,
    Extension,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext
    )
import src.logs as logs
from lookups.colors import Color
from src.database import Config, Data

class AutoSync(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # TODO: Add auto sync features

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    AutoSync(bot)