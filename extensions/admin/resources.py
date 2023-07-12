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

class Template(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    # Commands that update some resources
    resources = SlashCommand(name="resources", description="base resources command")
    config = SlashCommand(name="config", description="base config command")

    @config.subcommand(
        group_name="resources",
        group_description="resources group",
        sub_cmd_name="set-emojis-filepath",
        sub_cmd_description="Set the emojis filepath"
    )
    @slash_option(
        name="filepath",
        description="The filepath emojis will be saved in",
        required=True,
        opt_type=OptionType.STRING
    )
    async def config_set_emojis_filepath(self, ctx: SlashContext, filepath: str):
        Config.set_config_parameter("emojis_filepath", filepath)
        await send(ctx, f"Set the emojis directory filepath to: `{filepath}`")

    @resources.subcommand(
        group_name="update",
        group_description="update group",
        sub_cmd_name="emojis",
        sub_cmd_description="Re-downloads the latest set of emojis from twemoji"
    )
    async def update_emojis(self, ctx: SlashContext):
        message = await send(ctx, "Downloading emojis...", color=Color.YORANGE)
        
        download_dir = Directory("./downloads/")
        emojis_dir = Directory(Config.get_config_parameter("emojis_filepath"))

        # try:
        # Reset the downloads and emojis directory
        download_dir.delete()
        download_dir.create()

        # Delete emojis dir
        emojis_dir.delete()

        # Retrieve the latest release information from the Twemoji GitHub repository
        # from: https://github.com/jdecked/twemoji/releases/latest
        response = requests.get("https://api.github.com/repos/jdecked/twemoji/releases/latest")
        release_info = json.loads(response.text)
        
        # Get the download url
        download_url = release_info["zipball_url"]
        
        # Download the release
        response = requests.get(download_url)
        zip_file_path = os.path.join(download_dir.path, "twemoji_latest.zip")
        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)
        
        # Extract the downloaded zip file
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(download_dir.path)
        
        # Delete the zip file
        os.remove(zip_file_path)

        # Get extracted directory
        extracted_path = os.listdir(download_dir.path)[0]
        shutil.move(f"./downloads/{extracted_path}/assets/svg/", emojis_dir.path)
        download_dir.delete()
        
        await edit(message, "Latest Twemoji SVG images downloaded successfully.", color=Color.GREEN)
        # except Exception as e:
        #     await logs.DiscordLogger.log(self.bot, ctx, f"Failed to download Twemoji SVG images. Error: {str(e)}")

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Template(bot)