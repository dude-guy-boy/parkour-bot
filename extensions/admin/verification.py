# verification.py

from interactions import (
    Client,
    Extension,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    Button,
    ButtonStyle,
    Member,
    Role
    )
import src.logs as logs
from lookups.colors import Color
from src.database import Config, Data
from src.mojang import MojangAPI
from datetime import datetime
from asyncio import TimeoutError

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

    ### /VERIFY code ###
    @slash_command(
        name="verify",
        description="Link your minecraft account!"
    )
    @slash_option(
        name="code",
        description="The code you received when joining the verification server (play.parkourcentral.link)",
        opt_type=OptionType.STRING,
        required=True
    )
    async def verify(self, ctx: SlashContext, code: str):
        # Check if user is verified
        try:
            user = Data.get_data_item(key=str(ctx.author.id), table="verified")
            await ctx.send(embed=Embed(description=f"You're already verified as `{user['username']}`", color=Color.RED), ephemeral=True)
            return
        except:
            pass

        # Check if the code is in pending
        pending_list = Data.get_all_items(table="pending")

        for item in pending_list:
            # Check if its the entered code
            if not item['value']['phrase'].lower() == code.lower():
                continue

            # Check if the code has expired
            time = datetime.utcnow()
            generation_time = datetime.strptime(item['value']['time'], "%m/%d/%Y, %H:%M:%S")
            difference = time - generation_time

            Data.delete_item(item=item, table="pending")

            # If greater than an hour
            if difference.total_seconds() > 3600:
                await ctx.send(embed=Embed(description="Sorry, that code has expired!", color=Color.RED), ephemeral=True)
                return
            
            # If valid code add them to verified
            Data.set_data_item(key=str(ctx.author.id), value={"uuid": item['key'], "username": MojangAPI.get_name_from_uuid(item['key'])}, table="verified")
            await ctx.send(embed=Embed(description=f"You have been verified as `{MojangAPI.get_name_from_uuid(item['key'])}`", color=Color.GREEN), ephemeral=True)
            return
        
        await ctx.send(embed=Embed(description="That code could not be found!", color=Color.RED), ephemeral=True)

    ### /UNVERIFY ###
    @slash_command(
        name="unverify",
        description="Unlink your minecraft account"
    )
    async def unverify(self, ctx: SlashContext):
        # Check if user is verified
        try:
            user = Data.get_data_item(key=str(ctx.author.id), table="verified")
        except:
            await ctx.send(embed=Embed(description="You're not verified!", color=Color.RED), ephemeral=True)
            return

        confirm_buttons = [
            Button(style=ButtonStyle.DANGER, label="No, Cancel", custom_id="cancel_unverify"),
            Button(style=ButtonStyle.BLURPLE, label="Yes, I'm Sure", custom_id="confirm_unverify")
        ]

        confirmation_message = await ctx.send(embed=Embed(description="Are you sure you want to unverify your account? All progress in the points and economy systems will be lost!", color=Color.YORANGE), components=confirm_buttons, ephemeral=True)
        print(confirmation_message)

        try:
            decision = await Client.wait_for_component(self.bot, components=confirm_buttons, timeout=30)
            if decision.ctx.custom_id == "cancel_unverify":
                await ctx.edit(message=confirmation_message, embed=Embed(description="Unverification Cancelled", color=Color.GREEN), components=[])
                return
        except TimeoutError:
            # If it times out
            await ctx.edit(message=confirmation_message, embed=Embed(description="You took too long to decide!", color=Color.RED), components=[])
            return

        Data.delete_item(item={"key": str(ctx.author.id), "value": user}, table="verified")
        await ctx.edit(message=confirmation_message, embed=Embed(description=f"Unverified you from `{user['username']}`", color=Color.RED), components=[])

    ### /MANUAL-VERIFY user username ###
    @slash_command(
        name="manual-verify",
        description="Staff command to manually verify a user"
    )
    @slash_option(
        name="user",
        description="The user to manually verify",
        opt_type=OptionType.USER,
        required=True
    )
    @slash_option(
        name="username",
        description="The username of the account they are linking",
        opt_type=OptionType.STRING,
        required=True
    )
    async def manual_verify(self, ctx: SlashContext, user: Member, username: str):
        # check if user is verified already
        try:
            verified_user = Data.get_data_item(key=str(user.id), table="verified")
            await ctx.send(embed=Embed(description=f"{user.mention} is already verified as `{verified_user['username']}`", color=Color.RED))
            return
        except:
            pass

        # If username is valid, verify them
        if uuid := MojangAPI.get_uuid_from_name(username):
            username = MojangAPI.get_name_from_uuid(uuid)
            Data.set_data_item(key=str(user.id), value={"uuid": uuid, "username": username}, table="verified")
            await ctx.send(embed=Embed(description=f"Verified {user.mention} as `{username}`", color=Color.GREEN))

    ### /MANUAL-UNVERIFY user ###
    @slash_command(
        name="manual-unverify",
        description="Staff command to manually unverify a user"
    )
    @slash_option(
        name="user",
        description="The user to manually unverify",
        opt_type=OptionType.USER,
        required=True
    )
    async def manual_unverify(self, ctx: SlashContext, user: Member):
        # check if user is verified already
        try:
            verified_user = Data.get_data_item(key=str(user.id), table="verified")
            Data.delete_item(item={"key": str(user.id), "value": verified_user}, table="verified")
            await ctx.send(embed=Embed(description=f"Unverified {user.mention} as `{verified_user['username']}`", color=Color.GREEN))
        except:
            await ctx.send(embed=Embed(description=f"{user.mention} isn't verified", color=Color.RED))
            return

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Verification(bot)