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
from src.custompaginator import Paginator
from random import randint, choice
from interactions.models.internal.checks import TYPE_CHECK_FUNCTION

class Love(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()
        self.user_cache = []

    ### /CALCULATELOVE ###
    @slash_command(
        name="calculatelove",
        description="Calculate how much two users love each other",
    )
    @slash_option(
        name="user1",
        description="The first user",
        required=True,
        opt_type=OptionType.USER
    )
    @slash_option(
        name="user2",
        description="The second user",
        required=True,
        opt_type=OptionType.USER
    )
    async def calculate_love(self, ctx: SlashContext, user1: Member, user2: Member):
        if user1 == user2:
            await ctx.send(embed=Embed(description="You can't choose the same user twice!", color=Color.RED))
            return

        love_value = self.calculate_love_value(user1.id, user2.id)

        embed = Embed(color = self.rgb_to_hex(r = love_value*2.5))
        embed.add_field(name = "User1 💕", value = user1.mention, inline = True)
        embed.add_field(name = "🤔 Amount 🤔", value = f"😱 {love_value}% 😱", inline = True)
        embed.add_field(name = "💕 User2", value = user2.mention, inline = True)

        await ctx.send(embed=embed)

    ### /SOULMATE ###
    @slash_command(
        name="soulmate",
        description="Find your soulmates"
    )
    @slash_option(
        name="user",
        description="The user you want to get the soulmates of",
        opt_type=OptionType.USER,
        required=False
    )
    @slash_option(
        name="percentage",
        description="The percentage love you want to check for",
        opt_type=OptionType.INTEGER,
        required=False
    )
    async def soulmate(self, ctx: SlashContext, user: Member = None, percentage: int = 100):
        await ctx.defer()

        # Limit percentage
        if percentage > 100:
            percentage = 100
        if percentage < 1:
            percentage = 1

        # If user is not specified, do it for whoever sent the command
        if not user:
            user = ctx.member

        soulmates = []

        # Find soulmates
        for member in ctx.guild.members:
            love = self.calculate_love_value(member.id, user.id)
            if love == percentage:
                soulmates.append(member)

        # Send soulmates
        if_percentage = f" `{percentage}%` " if percentage != 100 else " "
        if_sender = f"You have" if user.id == ctx.author.id else f"{user.mention} has"
        if_sender_one_soulmate = f"Your" if user.id == ctx.author.id else f"{user.mention}'s"

        if not soulmates:
            await ctx.send(embed=Embed(description=f"{if_sender} no{if_percentage}soulmates!", color=Color.RED))
            return
        
        if len(soulmates) == 1:
            await ctx.send(embed=Embed(description=f"{if_sender_one_soulmate} only{if_percentage}soulmate is {soulmates[0].mention}!", color=Color.GREEN))
            return
        
        str_soulmates = "> " + "\n> ".join([soulmate.mention for soulmate in soulmates])
        if_sender = f"You have" if user.id == ctx.author.id else f"{user.display_name} has"

        soulmate_paginator = Paginator.create_from_string(self.bot, content=str_soulmates, num_lines=10, allow_multi_user=True)
        soulmate_paginator.default_button_color = ButtonStyle.GRAY
        soulmate_paginator.default_color = Color.GREEN
        soulmate_paginator.default_title = f"{if_sender} `{len(soulmates)}`{if_percentage}soulmates!"

        await soulmate_paginator.send(ctx)

        # await ctx.send(embed=Embed(description=f"{if_sender} `{len(soulmates)}`{if_percentage}soulmates! Here they all are:\n{str_soulmates}", color=Color.GREEN))

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

    ### /CHILDREN user ###
    @slash_command(
        name="children",
        description="Get a list of a users children"
    )
    @slash_option(
        name="user",
        description="The user you want to check the spouse of",
        opt_type=OptionType.USER,
        required=False
    )
    async def check_children(self, ctx: SlashContext, user: Member = None):
        if not user:
            user = ctx.member

        user_data = UserData.get_user(user.id)

        if not user_data or 'children' not in user_data:
            await ctx.send(embed=Embed(description=f"{user.mention} has no children!", color=Color.RED))
            return
        
        children = "> " + "\n> ".join([f"<@{child}>" for child in user_data["children"]])

        children_paginator = Paginator.create_from_string(
            self.bot,
            content=children,
            num_lines=10,
            allow_multi_user=True
            )
        children_paginator.default_button_color = ButtonStyle.GRAY
        children_paginator.default_color = Color.GREEN
        children_paginator.default_title = f"{user.display_name}'s Children"

        await children_paginator.send(ctx)

    ### /SPOUSE user ###
    @slash_command(
        name="spouse",
        description="Check who a user is married to"
    )
    @slash_option(
        name="user",
        description="The user you want to check the spouse of",
        opt_type=OptionType.USER,
        required=False
    )
    async def check_spouse(self, ctx: SlashContext, user: Member = None):
        if not user:
            user = ctx.member
        
        user_data = UserData.get_user(user.id)

        if not user_data or 'spouse' not in user_data:
            await ctx.send(embed=Embed(description=f"{user.mention} is not married!", color=Color.RED))
            return
        
        await ctx.send(embed=Embed(description=f"{user.mention} is married to <@{user_data['spouse']}>", color=Color.GREEN))

    ### /BABY ###
    @slash_command(
        name="baby",
        description="Try to make a baby with your spouse!"
    )
    async def baby(self, ctx: SlashContext):
        # Check if user is married
        user = UserData.get_user(ctx.author.id)

        if not user or 'spouse' not in user:
            await ctx.send(embed=Embed(description="You need to be married to try to make a baby!", color=Color.RED), ephemeral=True)
            return
        
        lover = user['spouse']

        # Send message where lover needs to press a button within 10s
        baby_button = Button(style=ButtonStyle.GRAY, emoji="👶", custom_id="make_baby")
        baby_embed = Embed(description=f"{ctx.author.mention} wants to try make a baby with <@{lover}>! <@{lover}> needs to press the button below within 10 seconds to try!", color=Color.GREEN)
        baby_message = await ctx.send(embed=baby_embed, components=baby_button)

        component = None

        try:
            component = await self.bot.wait_for_component(
                messages=baby_message,
                components=baby_button,
                timeout=10,
                check=self.is_lover()
            )

        except TimeoutError:
            baby_button.disabled = True
            baby_button.style = ButtonStyle.RED
            baby_embed.color = Color.RED

            await baby_message.edit(embed=baby_embed, components=baby_button)
            return
        
        # Baby button pressed
        if randint(1, 20) != 1:
            baby_button.style = ButtonStyle.RED
            baby_button.disabled = True
            baby_embed.color = Color.RED

            await component.ctx.edit_origin(embed=baby_embed, components=baby_button)

            await ctx.send(embed=Embed(description=f"Unlucky! <@{lover}> and {ctx.author.mention} weren't able to make a baby this time.", color=Color.RED))
            return
        
        # Edit baby message
        baby_button.style = ButtonStyle.GREEN
        baby_button.disabled = True

        await component.ctx.edit_origin(components=baby_button)

        # Get random other player to be the baby
        potential_babies = []
        all_users = UserData.get_all_items()
        all_children = [string for d in all_users if 'value' in d and 'children' in d['value'] for string in d['value']['children']] + [str(ctx.author.id), lover]
        all_children = list(set(all_children))

        # Only users who arent someones child already can be a new baby
        for member in ctx.guild.members:
            if str(member.id) not in all_children:
                potential_babies.append(str(member.id))
        
        the_baby = None

        try:
            the_baby = choice(potential_babies)
        except IndexError:
            await ctx.send(embed=Embed(description="There are no babies left to have!", color=Color.RED), ephemeral=True)
            return

        # Update user
        if 'children' not in user:
            user['children'] = [the_baby]
        else:
            user['children'].append(the_baby)

        UserData.set_user(ctx.author.id, data=user)

        # Update lover
        lover_data = UserData.get_user(lover)
        if 'children' not in lover_data:
            lover_data['children'] = [the_baby]
        else:
            lover_data['children'].append(the_baby)

        UserData.set_user(lover, data=lover_data)

        await ctx.send(embed=Embed(description=f"Congratulations! <@{lover}> and {ctx.author.mention} just had a baby and it's <@{the_baby}>!", color=Color.GREEN))

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
        
        lover = UserData.get_user(user["spouse"])

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

            await modal_ctx.send(embed=Embed(description=f"{ctx.author.mention} divorced <@{user['spouse']}> for reason:\n```{divorce_text}```", color=Color.RED))
            
            del lover["spouse"]
            UserData.set_user(user['spouse'], data=lover)

            del user["spouse"]
            UserData.set_user(ctx.author.id, data=user)
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

        lover = UserData.get_user(ctx.author.id)
        lover["spouse"] = proposer

        user = UserData.get_user(proposer)
        user["spouse"] = str(ctx.author.id)

        # Do accept stuff
        UserData.set_user(proposer, data=user)
        UserData.set_user(ctx.author.id, data=lover)
        UserData.delete_user(proposer, table="proposals")

    # Gets the proposer from proposal message button press
    def get_proposer(self, user_id, message):
        proposals = UserData.get_all_items(table="proposals")

        for proposal in proposals:
            if proposal['value']['pending'] == str(user_id) and proposal['value']['message_id'] == str(message.id):
                return proposal['key']

        return None

    # Calculates love value
    def calculate_love_value(self, user1, user2):
        a = int(str(user1)[-3:])
        b = int(str(user2)[-3:])

        love_value = str(a*b)
        return int(love_value[1:3]) + 1

    # Converts rgb to hex for calculatelove embed colour
    def rgb_to_hex(self, r = 0, g = 0, b = 0):
        return int(f"{int(r):02x}{int(g):02x}{int(b):02x}", 16)

    # Is lover check function, checks if the person who uses a component is the lover of the 
    def is_lover(self) -> TYPE_CHECK_FUNCTION:
        """
        Checks if the user who pressed the button is the right person
        """

        async def check(component) -> bool:
            spouse_id = component.ctx.message.embeds[0].description.split("@")[1].split(">")[0]
            spouse = UserData.get_user(spouse_id)

            if str(component.ctx.author.id) == spouse['spouse']:
                return True
            
            await component.ctx.send(embed=Embed(description="You aren't allowed to do that!", color=Color.RED), ephemeral=True)
            return False

        return check

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Love(bot)