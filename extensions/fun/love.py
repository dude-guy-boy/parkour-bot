# love.py

from interactions import (
    Button,
    ButtonStyle,
    Client,
    ComponentContext,
    Extension,
    ModalContext,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    Member,
    Modal,
    ParagraphText,
    component_callback
    )
import src.logs as logs
from lookups.colors import Color
from src.database import UserData
from interactions.models.internal.checks import TYPE_CHECK_FUNCTION

class Love(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### /CALCULATELOVE ###
    @slash_command(
        name="calculatelove",
        description="Calculate how much two users love each other",
    )
    @slash_option(
        name="user_1",
        description="The first user",
        required=True,
        opt_type=OptionType.USER
    )
    @slash_option(
        name="user_2",
        description="The second user",
        required=True,
        opt_type=OptionType.USER
    )
    async def calculate_love(self, ctx: SlashContext, user_1: Member, user_2: Member):
        if user_1 == user_2:
            await ctx.send(embed=Embed(description="You can't choose the same user twice!", color=Color.RED))
            return

        a = int(str(user_1.id)[-3:])
        b = int(str(user_2.id)[-3:])

        love_value = str(a*b)
        love_value = int(love_value[1:3]) + 1

        embed = Embed(color = self.rgb_to_hex(r = love_value*2.5))
        embed.add_field(name = "User1 💕", value = user_1.mention, inline = True)
        embed.add_field(name = "🤔 Amount 🤔", value = f"😱 {love_value}% 😱", inline = True)
        embed.add_field(name = "💕 User2", value = user_2.mention, inline = True)

        await ctx.send(embed=embed)

    # TODO: Soulmate command

    ### /PROPOSE TO ###
    @slash_command(
        name="propose",
        description="Propose to the love of your life!",
        sub_cmd_name="to",
        sub_cmd_description="Propose to the love of your life!"
    )
    @slash_option(
        name="lover",
        description="Name your lover.",
        opt_type=OptionType.USER,
        required=True
    )
    async def propose(self, ctx: SlashContext, lover: Member):
        if ctx.author.id == lover.id:
            await ctx.send(embed=Embed(description="You can't propose to yourself!", color=Color.RED), ephemeral=True)
            return

        # Get both users data
        user_data = UserData.get_user(ctx.author.id)
        lover_data = UserData.get_user(lover.user.id)

        # Check if user has a pending proposal
        user_proposals = UserData.get_user(ctx.author.id, table="proposals")
        if 'pending' in user_proposals:
            if user_proposals['pending'] == str(lover.id):
                await ctx.send(embed=Embed(description=f"You've already sent a proposal to <@{user_proposals['pending']}>!", color=Color.RED), ephemeral=True)
                return

            await ctx.send(embed=Embed(description=f"You can't propose to multiple people at the same time! You have a pending proposal to <@{user_proposals['pending']}>!", color=Color.RED), ephemeral=True)
            return

        # Check if the user is married
        if 'spouse' in user_data:
            await ctx.send(embed=Embed(description=f"You're already married to <@{user_data['spouse']}>!", color=Color.RED), ephemeral=True)
            return

        # Check if the lover is married
        if 'spouse' in lover_data:
            await ctx.send(embed=Embed(description=f"{lover.mention} is married to someone else.", color=Color.RED), ephemeral=True)
            return
        
        # Send modal prompting proposal message
        modal = Modal(
            ParagraphText(label=f"Enter your proposal message", custom_id="proposal_text", placeholder="Marry me baby!"),
            title="Proposal Form",
            custom_id="proposal_modal"
        )

        await ctx.send_modal(modal)

        try:
            modal_ctx: ModalContext = await self.bot.wait_for_modal(modal=modal, author=ctx.author)
            proposal_text = modal_ctx.responses['proposal_text']

            await modal_ctx.send(embed=Embed(description="Sending your proposal!", color=Color.GREEN), ephemeral=True)
        except:
            return

        # Send proposal
        accept_button = Button(style=ButtonStyle.GREEN, label="Accept Proposal", custom_id="accept_proposal")
        reject_button = Button(style=ButtonStyle.RED, label="Reject Proposal", custom_id="reject_proposal")

        proposal_embed = Embed(
                        description=f"{ctx.author.mention} is proposing to {lover.mention}!\n```{proposal_text}```",
                        color=Color.YORANGE,
                        footer="The proposee has 100s to respond!"
                        )

        proposal_message = await ctx.send(
                embed=proposal_embed,
                components=[accept_button, reject_button],
            )
        
        UserData.set_user(ctx.author.id, {"pending": str(lover.id), "message_id": str(proposal_message.id)}, table="proposals")

        # Timeout the proposal after 100s
        try:
            await self.bot.wait_for_component(
                messages=proposal_message,
                components=[accept_button, reject_button],
                timeout=100
                )
        except TimeoutError:
            timeout_button = Button(style=ButtonStyle.RED, label="Proposee took too long", disabled=True)

            proposal_embed.color = Color.RED
            await proposal_message.edit(embed=proposal_embed, components=timeout_button)

            UserData.delete_user(ctx.author.id, table="proposals")

    # TODO: /baby (some % chance of it working, baby will be another user)

    ### /DIVORCE ###
    @slash_command(
        name="divorce",
        description="Get a divorce"
    )
    async def divorce(self, ctx: SlashContext):
        user = UserData.get_user(ctx.author.id)
        
        # Check if user is not married
        if not user or 'spouse' not in user:
            await ctx.send(embed=Embed(description="You aren't married!", color=Color.RED), ephemeral=True)
            return

        # Prompt for reason
        modal = Modal(
            ParagraphText(label=f"Why do you want a divorce?", custom_id="divorce_text"),
            title="Divorce Form",
            custom_id="divorce_modal"
        )

        await ctx.send_modal(modal)

        try:
            modal_ctx: ModalContext = await self.bot.wait_for_modal(modal=modal, author=ctx.author)
            divorce_text = modal_ctx.responses['divorce_text']

            UserData.delete_user(ctx.author.id)
            UserData.delete_user(user['spouse'])

            await modal_ctx.send(embed=Embed(description=f"{ctx.author.mention} divorced <@{user['spouse']}> for reason:\n```{divorce_text}```", color=Color.RED))
        except:
            return

    ### Reject proposal component callback ###
    @component_callback("reject_proposal")
    async def rejection_callback(self, ctx: ComponentContext):
        # Check if it is the correct person pressing the button
        proposer = self.get_proposer(ctx.author.id, ctx.message)

        if not proposer:
            await ctx.send(embed = Embed(description="That proposal isn't addressed to you!", color=Color.RED), ephemeral=True)
            return

        # Proposal rejected
        # Ask for rejection reason
        modal = Modal(
            ParagraphText(label=f"What's your reason for rejecting?", custom_id="rejection_text", placeholder="I never loved you 😔"),
            title="Rejection Form",
            custom_id="rejection_modal"
        )

        await ctx.send_modal(modal)

        try:
            modal_ctx: ModalContext = await self.bot.wait_for_modal(modal=modal, author=ctx.author)
            rejection_text = modal_ctx.responses['rejection_text']

            # Get proposal message
            proposal_message_id = UserData.get_user(proposer, table="proposals")['message_id']
            proposal_message = await ctx.channel.fetch_message(int(proposal_message_id))

            # Edit proposal message
            accept_button = Button(style=ButtonStyle.GRAY, label="Accept Proposal", custom_id="accept_proposal", disabled=True)
            reject_button = Button(style=ButtonStyle.RED, label="Reject Proposal", custom_id="reject_proposal", disabled=True)

            proposal_embed = proposal_message.embeds[0]
            proposal_embed.color = Color.RED
            
            await proposal_message.edit(embed=proposal_embed, components=[accept_button, reject_button])

            # Send rejection message
            await modal_ctx.send(embed=Embed(title="The proposal was rejected :(", description=f"{ctx.author.mention} rejected <@{proposer}>'s proposal :pensive:\n```{rejection_text}```", color=Color.RED))
            UserData.delete_user(proposer, table="proposals")

        except:
            return

    ### Accept proposal component callback ###
    @component_callback("accept_proposal")
    async def accept_callback(self, ctx: ComponentContext):
        # Get the proposer
        proposer = self.get_proposer(ctx.author.id, ctx.message)

        if not proposer:
            await ctx.send(embed = Embed(description="That proposal isn't addressed to you!", color=Color.RED), ephemeral=True)
            return
        
        # Proposal accepted
        # Get proposal message
        proposal_message_id = UserData.get_user(proposer, table="proposals")['message_id']
        proposal_message = await ctx.channel.fetch_message(int(proposal_message_id))

        # Edit proposal message
        accept_button = Button(style=ButtonStyle.GREEN, label="Accept Proposal", custom_id="accept_proposal", disabled=True)
        reject_button = Button(style=ButtonStyle.GRAY, label="Reject Proposal", custom_id="reject_proposal", disabled=True)

        proposal_embed = proposal_message.embeds[0]
        proposal_embed.color = Color.GREEN
        
        await proposal_message.edit(embed=proposal_embed, components=[accept_button, reject_button])

        await ctx.send(embed=Embed(title="The proposal was accepted!", description=f"<@{proposer}> and {ctx.author.mention} just got MARRIED!!!\n👰🎉🍾🥂 Congratulations!! 🥂🍾🎉👰", color=Color.PINK))

        # Do accept stuff
        UserData.set_user(proposer, data={"spouse": str(ctx.author.id)})
        UserData.set_user(ctx.author.id, data={"spouse": proposer})
        UserData.delete_user(proposer, table="proposals")

    # Gets the proposer from proposal message button press
    def get_proposer(self, user_id, message):
        proposals = UserData.get_all_items(table="proposals")

        for proposal in proposals:
            if proposal['value']['pending'] == str(user_id) and proposal['value']['message_id'] == str(message.id):
                return proposal['key']

        return None

    # Converts rgb to hex for calculatelove embed colour
    def rgb_to_hex(self, r = 0, g = 0, b = 0):
        return int(f"{int(r):02x}{int(g):02x}{int(b):02x}", 16)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Love(bot)