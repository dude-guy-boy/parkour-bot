# tickets.py

from datetime import datetime
import os
from interactions import (
    Button,
    Client,
    ComponentContext,
    Extension,
    Message,
    PermissionOverwrite,
    Permissions,
    Role,
    SlashCommand,
    component_callback,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    )
from src.files import Directory
import src.logs as logs
from lookups.colors import Color
from src.database import Config, Data
from src.download import download
from src.ticketutil import Ticket, Transcribe
from src.customsend import send

class Tickets(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    config = SlashCommand(name="config", description="base config command")
    ticket = SlashCommand(name="ticket", description="base ticket command")

    @ticket.subcommand(
        group_name="open",
        group_description="Open a ticket",
        sub_cmd_name="points",
        sub_cmd_description="Open a points ticket to claim points"
    )
    async def open_points(self, ctx: SlashContext):        
        await ctx.defer(ephemeral=True)
        
        # Check if they are verified
        user = None
        try:
            user = Data.get_data_item(key=str(ctx.author.id), table="verified", name="verification")
        except:
            await ctx.send(embed=Embed(description="Only verified users can claim points! To learn how to verify your account, read the page on verification in /help", color=Color.RED), ephemeral=True)
            return
        
        # Generate channel name
        ticket_name = f"{user['username']}-points-ticket"
        identifier = f"{ctx.author.id} | Points Ticket"
        staff_roles = Config.get_config_parameter(key="staff_roles")

        # Get category
        category_id = Config.get_config_parameter("point_ticket_category_id")

        # Check if they already have a ticket open
        existing_ticket = await Ticket.fetch_ticket(ctx, identifier, category_id)

        if(existing_ticket):
            embed = Embed(
                description=f"{ctx.author.mention}, you already have a points ticket open: {existing_ticket.mention}", color=Color.YORANGE)
            await ctx.send(embeds=embed, ephemeral=True)
            return

        # Make overwrites
        overwrites = [
            # Make @everyone unable to view the channel
            PermissionOverwrite(id=int(ctx.guild_id), type=0, deny=Permissions.VIEW_CHANNEL),
            # Allow user who created ticket to view and send messages in the channel
            PermissionOverwrite(id=int(ctx.author.user.id), type=1, allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES | Permissions.ATTACH_FILES),
            # Allow role to view and send messages
            PermissionOverwrite(
                id=staff_roles["helper"], type=0, allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES),
            PermissionOverwrite(
                id=staff_roles["moderator"], type=0, allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES),
            PermissionOverwrite(
                id=staff_roles["developer"], type=0, allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES),
            PermissionOverwrite(   
                id=staff_roles["admin"], type=0, allow=Permissions.VIEW_CHANNEL | Permissions.SEND_MESSAGES)
        ]

        ticket = await Ticket.create(ctx, name=ticket_name, overwrites=overwrites, category=category_id, identifier=identifier)

        msg_embed = Embed(title="Claim Points", description="This channel has been created for you to claim points for your map completions.", color=Color.WHITE)
        msg_embed.add_field(name="Instructions", value="Send all your map completion evidence in this channel. Staff will be with you shortly, and once have dealt with all your submissions, you may press the `Close Ticket` button below this message, or use the `/ticket close` command.\n\n`NOTE:` Try to have everything you need to submit ready before opening a ticket (screenshots, videos, etc). If you're unsure you can see what type of proof a map needs with `/map info <map>`. Its also helpful for staff if you list the completions you are submitting all in one message!")
        msg_embed.add_field(name="Some Useful Commands", value="`/profile <user>` See your (or anyone elses) point total and get information about past completions.\n`/leaderboard points <filters>` View overall or per-type leaderboards and see where you're placed on them!")

        close_button = Button(
            style=ButtonStyle.DANGER,
            label="Close Ticket",
            custom_id="close_ticket"
        )

        await ticket.send(embeds=msg_embed, components=close_button)

        embed = Embed(
            description=f"Here's your new points ticket: <#{ticket.id}>", color=Color.GREEN)
        await ctx.send(embeds=embed, ephemeral=True)

        await logs.DiscordLogger.log(self.bot, ctx, f"Created a new points ticket for {ctx.author.mention}")
        self.logger.info(f"Created a new points ticket for {ctx.author.user.username}#{ctx.author.user.discriminator}")

    @component_callback("close_ticket")
    async def close_ticket_callback(self, ctx: ComponentContext):
        # Exit if channel isnt a ticket
        if not Ticket.is_ticket(ctx.channel):
            await send(ctx, "This channel isnt a ticket!", color=Color.RED, ephemeral=True)
            return
        
        # The channel is a ticket, get the owner
        owner_id = Ticket.get_owner_id(ctx.channel)
        owner = await ctx.guild.fetch_member(owner_id)

        # Get transcript dump path and create if doesnt exist
        dump_dir = Directory(Config.get_config_parameter("transcript_dump_path"))
        attachments_dir = Directory(os.path.relpath(dump_dir.path) + "/attachments")
        dump_dir.create()
        attachments_dir.create()

        # Retrieve all messages and users who participated in the ticket
        ticket_messages: list[Message] = []
        ticket_users = []
        replied_message_ids = []
        replied_messages = {}
        roles = {}
        channels = {}
        users = {}
        
        message: Message
        async for message in ctx.channel.history(limit=0):
            ticket_messages.append(message)

            # Save list of participating users
            if message.author not in ticket_users:
                ticket_users.append(message.author)

            # Save list of replied messages
            if message._referenced_message_id:
                replied_message_ids.append(int(message._referenced_message_id))

            async for member in message.mention_users:
                users[str(member.user.id)] = str(member.username)

            for channel in message.mention_channels:
                channels[str(channel.id)] = str(channel.name)

            async for role in message.mention_roles:
                roles[str(role.id)] = (str(role.name), str(role.color.hex))

        for message in ticket_messages:
            if int(message.id) in replied_message_ids:
                replied_messages[int(message.id)] = message

        # Make html profiles for each participating user
        user_map = {}
        user_profiles = []

        for idx, user in enumerate(ticket_users):
            user_ref_name = f"user{idx}"
            user_map[int(user.id)] = user_ref_name
            user_profiles.append(Transcribe.make_profile(user, user_ref_name))

        # Make all the messages html
        messages = []

        for message in ticket_messages:
            for attachment in message.attachments:
                # Download and save the attachments if they havent already been

                attachment_path = f"{attachments_dir.path}/{attachment.id}.{attachment.filename.split('.')[-1]}"
                if f"{attachment.id}.{attachment.filename.split('.')[-1]}" not in os.listdir(attachments_dir.path):
                    await download(attachment.url, attachment_path)

            messages.append(await Transcribe.make_message(message, user_map, replied_messages, attachments_dir.path, roles, channels, users))

        time = datetime.utcnow()

        # Combine into final html document
        html = Transcribe.make_transcript_html(owner, user_profiles, messages, time)

        file_time_format = time.strftime("%d-%m-%Y_%H-%M-%S")
        with open(f"{dump_dir.path}/{owner_id}-{file_time_format}.html", "w") as file:
            # Write the string to the file
            file.write(html)

        #TODO: Close ticket
        

    @component_callback("claim_points")
    async def claim_points_callback(self, ctx: ComponentContext):
        # TODO: Create points ticket
        pass

    @slash_command(
        name="send-ticket-button",
        description="Send an 'open points ticket' button in chat"
    )
    async def send_ticket_button(self, ctx: SlashContext):
        ticket_button = Button(
            style=ButtonStyle.PRIMARY,
            label="Claim Points",
            custom_id="claim_points"
        )
        await ctx.channel.send(components = ticket_button)
        await ctx.send("Sent!", ephemeral = True)

    # TODO: Add logging to all config

    @config.subcommand(
        group_name="tickets",
        group_description="config for tickets",
        sub_cmd_name="set-points-category",
        sub_cmd_description="Set the category points tickets should be created in"
    )
    @slash_option(
        name="category",
        description="The category you want to set",
        opt_type=OptionType.CHANNEL,
        required=True
    )
    async def config_set_points_category(self, ctx: SlashContext, category):
        Config.set_config_parameter(key="point_ticket_category_id", value=str(category.id))
        await ctx.send(embed=Embed(description=f"Set the category to {category.mention}", color=Color.GREEN), ephemeral=True)

    @config.subcommand(
        group_name="tickets",
        group_description="config for tickets",
        sub_cmd_name="transcript-dump-path",
        sub_cmd_description="Set the dump location for transcript files"
    )
    @slash_option(
        name="path",
        description="The filepath you want to set",
        opt_type=OptionType.STRING,
        required=True
    )
    async def config_set_transcript_dump_path(self, ctx: SlashContext, path):
        Config.set_config_parameter(key="transcript_dump_path", value=path)
        await ctx.send(embed=Embed(description=f"Set the path to `{path}`", color=Color.GREEN), ephemeral=True)

    @config.subcommand(
        group_name="tickets",
        group_description="config for tickets",
        sub_cmd_name="set-staff-roles",
        sub_cmd_description="Set the staff roles"
    )
    @slash_option(
        name="helper",
        description="The helper role",
        opt_type=OptionType.ROLE,
        required=True
    )
    @slash_option(
        name="moderator",
        description="The moderator role",
        opt_type=OptionType.ROLE,
        required=True
    )
    @slash_option(
        name="developer",
        description="The developer role",
        opt_type=OptionType.ROLE,
        required=True
    )
    @slash_option(
        name="admin",
        description="The admin role",
        opt_type=OptionType.ROLE,
        required=True
    )
    async def config_set_staff_roles(self, ctx: SlashContext, helper: Role, moderator: Role, developer: Role, admin: Role):
        Config.set_config_parameter(key="staff_roles", value={'helper': int(helper.id), 'moderator': int(moderator.id), 'developer': int(developer.id), 'admin': int(admin.id)})
        await ctx.send(embed=Embed(description=f"Set the staff roles: {helper.mention}, {moderator.mention}, {developer.mention}, {admin.mention}", color=Color.GREEN), ephemeral=True)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Tickets(bot)