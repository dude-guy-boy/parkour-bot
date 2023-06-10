# 45.py

from interactions import (
    Client,
    Extension,
    cooldown,
    Buckets,
    Embed
    )
import src.logs as logs
from src.database import UserData
from lookups.colors import Color
from interactions.ext.hybrid_commands import hybrid_slash_command, HybridContext
from random import randint

class FourtyFive(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    @hybrid_slash_command(
        name="45",
        description="Do a 45 strafe, test your luck!"
    )
    @cooldown(
        bucket=Buckets.USER,
        rate=1,
        interval=300
    )
    async def fourty_five(self, ctx: HybridContext):
        user = UserData.get_user(str(ctx.author.id))

        if not user:
            user = {
                "wins": 0,
                "attempts": 0
            }

        random_number = randint(0, 900) / 10

        if(random_number == 45):
            await ctx.send(embed=Embed(description=f"{ctx.author.mention} 🔥🔥🔥🔥🔥🔥 PERFECT 45 💯💯💯💯💯💯 YOUR 45 WAS 45.0! 🤑🤑🤑🤑🤑🤑", color=Color.GREEN))
            UserData.set_user(str(ctx.author.id), {"wins": user['wins']+1, "attempts": user['attempts']+1})
            return

        await ctx.send(embeds=Embed(description=f"{ctx.author.mention} Not a perfect 45 noob, {random_number}", color=Color.YORANGE))
        UserData.set_user(str(ctx.author.id), {"wins": user['wins'], "attempts": user['attempts']+1})
        

    # TODO: Add leaderboard
    
def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    FourtyFive(bot)