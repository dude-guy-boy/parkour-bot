# verification.py

from interactions import (
    Client,
    Extension,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext,
    Role
    )
import src.logs as logs
from src.colors import Color
from src.database import Config, Data

class Verification(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### CONFIG verified role ###
    @slash_command(
        name="config",
        description="base config command",
        group_name="verification",
        group_description="verification group command",
        sub_cmd_name="set-role",
        sub_cmd_description="Set the role that verified users will get"
    )
    @slash_option(
        name="role",
        description="The role that verified users will get",
        required=True,
        opt_type=OptionType.ROLE
    )
    async def config_verification_set_role(self, ctx: SlashContext, role: Role):
        Config.set_config_parameter("verified_role_id", value=role.id)
        await ctx.send(embed=Embed(description=f"Set the verified role to: {role.mention}", color=Color.GREEN))

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Verification(bot)