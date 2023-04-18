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
    Member
    )
import src.logs as logs
from src.colors import Color

class Love(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

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

        embed = Embed(color = 0xfc4242)
        embed.add_field(name = "User1 💕", value = user_1.mention, inline = True)
        embed.add_field(name = "🤔 Amount 🤔", value = f"😱 {love_value}% 😱", inline = True)
        embed.add_field(name = "💕 User2", value = user_2.mention, inline = True)

        await ctx.send(embed=embed)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Love(bot)