# resources.py

import json
import shutil
from interactions import (
    Client,
    Extension,
    slash_option,
    SlashContext,
    OptionType,
    SlashCommand
    )
import requests
import src.logs as logs
from lookups.colors import Color
from src.database import Config
from src.customsend import send, edit
from src.files import Directory
import zipfile
import os

class Resources(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # Commands that update some resources
    # resources = SlashCommand(name="resources", description="base resources command")
    
def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Resources(bot)