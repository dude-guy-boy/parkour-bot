# template.py

### This is a template extension ###

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
from src.colors import Color
import os.path as path
from tinydb import TinyDB, Query

class Template(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

        # Uncomment if storing data
        # self.users = TinyDB(f"./data/{path.basename(__file__)[:-3]}.json").table("users")
        # self.user = Query()

    @slash_command(
        name="template-command",
        description="Just a template command",
    )
    @slash_option(
        name="opt_one",
        description="Template option",
        required=True,
        opt_type=OptionType.STRING
    )
    async def template_command(self, ctx: SlashContext, opt_one: str):
        await ctx.send(embed=Embed(description=f"Sent from a template command! `{opt_one}`", color=Color.GREEN))

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Template(bot)