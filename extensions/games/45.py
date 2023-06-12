# 45.py

from interactions import (
    Client,
    Extension,
    SlashContext,
    cooldown,
    Buckets,
    Embed,
    slash_command,
    ButtonStyle
    )
import src.logs as logs
from src.database import UserData
from lookups.colors import Color
from interactions.ext.hybrid_commands import hybrid_slash_command, HybridContext
from random import randint
from src.leaderboard import Leaderboard

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

        if random_number == 45:
            message = await ctx.send(embed=Embed(description=f"{ctx.author.mention} 🔥🔥🔥🔥🔥🔥 PERFECT 45 💯💯💯💯💯💯 YOUR 45 WAS 45.0! 🤑🤑🤑🤑🤑🤑", color=Color.GREEN))
            UserData.set_user(str(ctx.author.id), {"wins": user['wins']+1, "attempts": user['attempts']+1})

            self.logger.info(f"{ctx.author.username} just did a perfect 45")
            await logs.DiscordLogger.log(bot=self.bot, description=f"{ctx.author.username} [just did a perfect 45]({message.jump_url})")
            return

        await ctx.send(embeds=Embed(description=f"{ctx.author.mention} Not a perfect 45 noob, {random_number}", color=Color.YORANGE))
        UserData.set_user(str(ctx.author.id), {"wins": user['wins'], "attempts": user['attempts']+1})

    @slash_command(
        name="leaderboard",
        description="base leaderboard command",
        group_name="game",
        group_description="game group command",
        sub_cmd_name="45",
        sub_cmd_description="View the 45 strafe leaderboard!"
    )
    async def leaderboard(self, ctx: SlashContext):
        data = UserData.get_all_items()
        data = [{"user": f"<@{item['key']}>", "wins": item['value']['wins'], "attempts": item['value']['attempts']} for item in data]

        # Create the leaderboard
        lb = Leaderboard.create(
            client=self.bot,
            data=data,
            field_map={"Leaderboard": "user", "Wins": "wins", "Attempts": "attempts"},
            sort_by="wins",
            secondary_sort_by="attempts",
            secondary_descending=False,
            title="45 Strafe Leaderboard",
            text=f"There are `{len(data)}` users who've cumulatively done `{sum([user['wins'] for user in data])}` perfect 45.0° strafes."
        )

        await lb.send(ctx)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    FourtyFive(bot)