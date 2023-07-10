from interactions import Embed, InteractionContext
from lookups.colors import Color

async def send(ctx: InteractionContext, content: str, color: int = Color.GREEN, ephemeral: bool = False):
    return await ctx.send(embed=Embed(description=content, color=color), ephemeral=ephemeral)