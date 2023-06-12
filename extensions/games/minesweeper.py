# minesweeper.py

from interactions import (
    Button,
    Client,
    Extension,
    listen,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext
    )
from interactions.ext.hybrid_commands import hybrid_slash_command, HybridContext
from interactions.api.events.internal import Component
import src.logs as logs
from lookups.colors import Color
from src.database import UserData
from random import randint
from src.leaderboard import Leaderboard

class Minesweeper(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### /MINESWEEPER ###
    @hybrid_slash_command(
        name="minesweeper",
        description="Play a game of minesweeper!"
    )
    async def minesweeper(self, ctx: HybridContext):
        # Defer if slash command
        if ctx.prefix == "/":
            await ctx.defer()

        # Get user data
        user = UserData.get_user(ctx.author.id)

        # If user has an existing game, re-send it
        if user and user["message"]:
            # Delete the old game message
            try:
                old_channel = await self.bot.fetch_channel(user["channel"])
                old_message = await old_channel.fetch_message(user["message"])
                await old_message.delete()
            except:
                pass
            
            # Count the number of mines in their existing game
            try:
                num_mines = sum([row.count(True) for row in user["mines"]])
            except:
                num_mines = "?"

            # Re-send the game
            embed = Embed(
                description=f"{ctx.author.mention} here's your existing game of minesweeper!\nThere are `{num_mines}` mines.", color=Color.GREEN)

            new_message = await ctx.send(embeds=embed, components=self.generate_buttons(user["mines"], user["revealed"]))

            # Update the message
            user["message"] = int(new_message.id)
            user["channel"] = int(new_message.channel.id)

            UserData.set_user(ctx.author.id, user)
            return

        # Generate buttons
        buttons = self.generate_buttons(None, None)

        # Send board
        embed = Embed(
            description=f"{ctx.user.mention} here's your Minesweeper board!\nThere are `?` mines.", color=Color.GREEN)
        msg = await ctx.send(embeds=embed, components=buttons)

        if not user:
            user = {"mines": None, "revealed": None,
                    "message": None, "channel": None}

        user["mines"] = None
        user["revealed"] = None
        user["message"] = int(msg.id)
        user["channel"] = int(msg.channel.id)

        UserData.set_user(ctx.author.id, user)

    ### Minesweeper Button Listener ###
    @listen("on_component")
    async def minesweeper_listener(self, component: Component):
        # Ignore non minesweeper buttons
        if not component.ctx.custom_id.startswith("minesweeper"):
            return
        
        ctx = component.ctx
        custom_id = ctx.custom_id
        
        # If they click an exploded mine or an avoided mine, start a new game for them
        if(custom_id.endswith("dead") or custom_id.endswith("won")):
            await self.minesweeper(ctx)
            return

        # Get minesweeper user
        user = UserData.get_user(ctx.author.id)

        # Check if button presser is the game owner
        if not user or user["message"] != int(ctx.message.id):
            await ctx.send(embeds=Embed(description="That isn't your minesweeper game!", color=Color.RED), ephemeral=True)
            
            if not user:
                UserData.delete_user(ctx.author.id)
            return
        
        board = user["mines"]
        revealed = user["revealed"]
        buttons = None

        # Get coordinate of button pressed
        coord = (int(custom_id[12:13]), int(custom_id[13:]))

        # If the board has not yet been initialised, initialise it
        if not board:
            board, revealed = self.init_board(coord)

        game_over = False
        won_game = False

        if board:
            if board[coord[0]][coord[1]]:
                # The user hit a mine, game over
                game_over = True
            else:
                revealed = self.reveal_cell(board, revealed, coord)
        
        # Check if game has been won
        inverse_revealed = []
        for row in revealed:
            inverse_revealed.append([not item for item in row])

        # Won game
        if board == inverse_revealed:
            won_game = True

        # Get number of mines on the board
        num_mines = sum([row.count(True) for row in board])

        buttons = self.generate_buttons(board, revealed, game_over = game_over, won_game = won_game, exploded = coord if game_over else None)

        # Update mines and revealed matrices
        user["mines"] = board
        user["revealed"] = revealed

        embed = Embed(description=f"{ctx.user.mention} here's your Minesweeper board!\nThere are `{num_mines}` mines.", color=Color.GREEN)

        UserData.set_user(ctx.author.id, user)

        if game_over:
            embed = Embed(description=f"💥 {ctx.user.mention} You Exploded! 💥", color=Color.RED)
            embed.set_footer(text="Click on the exploded mine to play again!")
            UserData.delete_user(ctx.author.id)

        if won_game:
            embed = Embed(description=f"🎉 {ctx.user.mention} You Won! 🎉\n`+{num_mines} mines avoided`", color=Color.GREEN)
            embed.set_footer(text="Click on an avoided mine to play again!")
            UserData.delete_user(ctx.author.id)
            leaderboard_user = UserData.get_user(ctx.author.id, table="leaderboard")

            if not leaderboard_user:
                leaderboard_user = {"mines_avoided": num_mines, "most_mines": 0}
            else:
                leaderboard_user["mines_avoided"] += num_mines

            if num_mines > int(leaderboard_user["most_mines"]):
                leaderboard_user["most_mines"] = num_mines

            UserData.set_user(ctx.author.id, leaderboard_user, table="leaderboard")
        
        await ctx.edit_origin(embeds=embed, components=buttons)

    # Generate buttons for minsweeper board
    def generate_buttons(self, mine_array, revealed, is_disabled=False, game_over=False, won_game = False, exploded = None):
        buttons = []
        for i in range(5):
            row = []
            for j in range(5):
                if won_game:
                    if mine_array[i][j] and not revealed[i][j]:
                        row.append(Button(
                            style=ButtonStyle.SUCCESS, label="💣", custom_id=f"minesweeper_{i}{j}_won", disabled=False))
                        continue

                    cell_value = self.compute_cell_value(mine_array, (i, j))
                    label = "‎"
                    if cell_value != 0:
                        label = str(cell_value)

                    row.append(Button(
                        style=ButtonStyle.PRIMARY, label=label, custom_id=f"minesweeper_{i}{j}", disabled=True))
                    continue

                if game_over:
                    if exploded:
                        if (i, j) == exploded:
                            row.append(Button(
                                style=ButtonStyle.DANGER, label="💥", custom_id=f"minesweeper_{i}{j}_dead"))
                            continue

                    if mine_array[i][j] and not revealed[i][j]:
                        row.append(Button(
                            style=ButtonStyle.SECONDARY, label="💣", custom_id=f"minesweeper_{i}{j}_dead", disabled=True))
                        continue

                    cell_value = self.compute_cell_value(mine_array, (i, j))
                    label = "‎"
                    if cell_value != 0:
                        label = str(cell_value)

                    if revealed[i][j]:
                        row.append(Button(
                            style=ButtonStyle.PRIMARY, label=label, custom_id=f"minesweeper_{i}{j}", disabled=True))
                        continue

                    row.append(Button(
                        style=ButtonStyle.SECONDARY, label=label, custom_id=f"minesweeper_{i}{j}", disabled=True))
                    continue

                if not mine_array or not revealed[i][j]:
                    row.append(Button(
                        style=ButtonStyle.SECONDARY, label="‎", custom_id=f"minesweeper_{i}{j}", disabled=is_disabled))
                    continue

                if revealed[i][j]:
                    cell_value = self.compute_cell_value(mine_array, (i, j))
                    label = "‎"
                    if cell_value != 0:
                        label = str(cell_value)

                    row.append(Button(
                        style=ButtonStyle.SECONDARY, label=label, custom_id=f"minesweeper_{i}{j}", disabled=True))

            buttons.append(row)

        return buttons
    
    # Initialise the board
    def init_board(self, cell_coordinate):
        board = [[False] * 5 for _ in range(5)]
        revealed = [[False] * 5 for _ in range(5)]

        revealed[cell_coordinate[0]][cell_coordinate[1]] = True

        num_mines = 2
        for i in range(23):
            if randint(1, 5) == 1:
                num_mines += 1

        while(sum([row.count(True) for row in board]) < num_mines):
            row = randint(0,4)
            col = randint(0,4)
            if not revealed[row][col]:
                board[row][col] = True

        return board, revealed

    # Reveal a cell
    def reveal_cell(self, board, revealed, cell_coordinate):
        # Reveal the cell
        revealed[cell_coordinate[0]][cell_coordinate[1]] = True

        # If the revealed cell is a 0
        if self.compute_cell_value(board, cell_coordinate) == 0:
            # If any cell is adjacent to a revealed cell with a value of 0, reveal it
            for k in range(10):
                for i in range(5):
                    for j in range(5):
                        # Check if cell is adjacent to a revealed 0
                        if self.adjacent_to_revealed_0(board, revealed, (i, j)):
                            revealed[i][j] = True

        return revealed

    # Checks if a given cell is adjacent to a 0 cell that has been revealed
    def adjacent_to_revealed_0(self, mine_array, revealed, cell_coordinate):
        offsets = self.compute_checkable_offsets(cell_coordinate)

        for offset in offsets:
            check_coord = (cell_coordinate[0]+offset[0], cell_coordinate[1]+offset[1])
            if revealed[check_coord[0]][check_coord[1]]:
                if self.compute_cell_value(mine_array, check_coord) == 0:
                    return True

        return False

    # Calculates the value of a cell based on the surrounding 8 cells
    def compute_cell_value(self, mine_array, cell_coordinate):
        cell_value = 0
        offsets = self.compute_checkable_offsets(cell_coordinate)

        for offset in offsets:
            if mine_array[cell_coordinate[0]+offset[0]][cell_coordinate[1]+offset[1]]:
                cell_value += 1

        return cell_value

    # Based on the cell location returns the offsets from it that within the board
    def compute_checkable_offsets(self, cell_coordinate):
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        # Remove impossible offsets
        if cell_coordinate[0] == 0:
            # Cant check cells above
            remove_offsets = [(-1, -1), (-1, 0), (-1, 1)]
            for offset in remove_offsets:
                try:
                    offsets.remove(offset)
                except:
                    pass

        if cell_coordinate[0] == 4:
            # Cant check cells below
            remove_offsets = [(1, -1), (1, 0), (1, 1)]
            for offset in remove_offsets:
                try:
                    offsets.remove(offset)
                except:
                    pass

        if cell_coordinate[1] == 0:
            # Cant check cells to the left
            remove_offsets = [(-1, -1), (0, -1), (1, -1)]
            for offset in remove_offsets:
                try:
                    offsets.remove(offset)
                except:
                    pass

        if cell_coordinate[1] == 4:
            # Cant check cells to the right
            remove_offsets = [(-1, 1), (0, 1), (1, 1)]
            for offset in remove_offsets:
                try:
                    offsets.remove(offset)
                except:
                    pass
        
        return offsets

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Minesweeper(bot)