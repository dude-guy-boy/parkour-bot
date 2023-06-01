# manager.py

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

class Manager(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # TODO: Add management commands
    # Bot restart
    # Bot reload
    # Bot update
    # Force backup
    # Get backup
    # Get logs

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Manager(bot)