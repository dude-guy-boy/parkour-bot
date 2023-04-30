# spiritanimal.py

from interactions import (
    Client,
    Extension,
    slash_command,
    SlashContext,
    Embed
    )
from interactions.ext.prefixed_commands import prefixed_command, PrefixedContext
import src.logs as logs
from src.colors import Color
from lookups.animals import Animals
from math import floor

class SpiritAnimal(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    async def spirit_animal(self, ctx):
        id = int(str(ctx.user.id)[12:15])
        number = floor(id * (len(Animals) / 1000) - 1)
        animal = Animals[number]
        embed = Embed(description = f"{ctx.author.mention} your spirit animal is a: :scream: **{animal}** :scream:", color = Color.YORANGE)
        await ctx.send(embeds = embed)

    @slash_command(
        name="spirit",
        description="spirit animal base command",
        sub_cmd_name="animal",
        sub_cmd_description="What's your spirit animal??"
    )
    async def spirit_animal_command(self, ctx: SlashContext):
        await self.spirit_animal(ctx)

    @prefixed_command("spiritanimal")
    async def spirit_animal_prefixed_command(self, ctx: PrefixedContext):
        await self.spirit_animal(ctx)

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    SpiritAnimal(bot)