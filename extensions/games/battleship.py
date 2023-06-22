# battleship.py

import asyncio
from interactions import (
    Button,
    Client,
    Extension,
    Message,
    listen,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext
    )
from interactions.api.events.internal import Component
import src.logs as logs
from lookups.colors import Color
from src.database import UserData
from random import randint, choice

class Battleship(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    @slash_command(
        name="test",
        description="desc"
    )
    async def test_func(self, ctx: SlashContext):
        user = UserData.get_user(ctx.author.id)
        thing = self.make_move(user['board'], user['ships'])

    ### /BATTLESHIP ###
    @slash_command(
        name="battleship",
        description="Play a game of battleship!",
    )
    async def play_battleship(self, ctx: SlashContext):
        user = UserData.get_user(ctx.author.id)

        # If the user has an existing game, send it
        if 'board' in user:
            embed = Embed(description=f"{ctx.user.mention} here's your existing Battleship game!", color=Color.GREEN)

            # Check if the game was started
            if not self.game_begun(user['revealed'], user['bot_revealed']):
                embed.set_footer("Click on water to re-randomise, or on a ship to begin!")

            # Get and delete the old message
            old_message_channel = await ctx.guild.fetch_channel(user['message']['channel_id'])
            old_message = await old_message_channel.fetch_message(user['message']['message_id'])
            await old_message.delete()

            # Send the new message with the old board
            new_message = await ctx.send(embed=embed, components=self.generate_buttons(user['board'], user['revealed']))

            # Save the new message
            user['message'] = {"message_id": str(new_message.id), "channel_id": str(new_message.channel.id)}
            UserData.set_user(ctx.author.id, user)
            return
        
        if not user:
            user = {}

        # Generate new board
        new_board = self.generate_random_board()
        revealed = [[0] * 5 for _ in range(5)]

        # Send board
        buttons = self.generate_buttons(new_board, revealed)
        embed = Embed(description=f"{ctx.user.mention} here's your Battleship board!", footer="Click on water to re-randomise, or on a ship to begin!", color=Color.GREEN)
        msg = await ctx.send(embeds=embed, components=buttons)

        # Set started
        user['started'] = False

        # Save user and bot boards
        user['board'] = new_board
        user['bot'] = self.generate_random_board()

        # Randomly decide if the user or the bot will start
        user['turn'] = choice(("bot", "user"))

        # Save user and bot revealed boards
        user['revealed'] = revealed
        user['bot_revealed'] = revealed

        # Save message info
        user['message'] = {"message_id": str(msg.id), "channel_id": str(msg.channel.id)}
        UserData.set_user(ctx.author.id, user)

    ### Battleship Button Listener ###
    @listen("on_component")
    async def battleship_listener(self, component: Component):
        # Ignore non battleship buttons
        if not component.ctx.custom_id.startswith("battleship"):
            return
        
        ctx = component.ctx
        custom_id = ctx.custom_id

        # Get battleship user
        user = UserData.get_user(ctx.author.id)

        # Check if button presser is the game owner
        if not user or user["message"]['message_id'] != str(ctx.message.id):
            await ctx.send(embeds=Embed(description="That isn't your battleship game!", color=Color.RED), ephemeral=True)
            
            if not user:
                UserData.delete_user(ctx.author.id)
            return

        # Get coordinate of button pressed
        coord = (int(custom_id[11:12]), int(custom_id[12:]))

        # Check if the game has started
        if not self.game_begun(user['revealed'], user['bot_revealed']):
            # Check if they clicked a ship
            if self.check_ship(coord, user['board']):

                # If the bot should start
                if user['turn'] == "bot":
                    # Disable buttons and say that pk bot is making the first move
                    disabled_message: Message = await ctx.edit_origin(
                        embed=Embed(description=f"The game has now begun. {self.bot.user.mention} will make the first move.", color=Color.YORANGE),
                        components=self.generate_buttons(user['board'], user['revealed'], disable_all=True)
                    )

                    # Wait a second to appear like its thinking
                    await asyncio.sleep(1)

                    # Make the move

                    # Prompt player to click anywhere when they are ready to make their move

                    # updated_board = self.make_move(user['board'])

                    # TODO: Calculate result of pk bots move
                    # await disabled_message.edit(embed=Embed(description=f"piss"))
                    return

                # The user should syart
                await ctx.edit_origin(embed=Embed(description=f"The game has now begun. Please make the first move.", color=Color.GREEN))
                return
            
            # If they clicked water, regenerate their board
            user['board'] = self.generate_random_board()
            UserData.set_user(ctx.author.id, user)

            # Send regenerated board
            buttons = self.generate_buttons(user['board'], user['revealed'])
            await ctx.edit_origin(components=buttons)
            return

        # Check if its the users turn
        if user['turn'] == "bot":
            await ctx.send(embeds=Embed(description="It's not your turn!", color=Color.RED), ephemeral=True)
            return

    # Makes a move
    # def make_move(self, board, ship_positions):
    #     # TODO: Make move
    #     # Get all coordinates for all valid positions
    #     valid_coords = self.get_all_valid_coords(board, ship_positions)

    #     # If there are no hits choose a random valid coord
    #     if not any(6 in sublist or 7 in sublist for sublist in board):
    #         return choice(valid_coords)

    #     # If there is a hit that hasnt sunk a ship, choose a valid adjacent spot
    #     all_hits = self.get_all_hits(board, ship_positions)
    #     decision = choice(all_hits)
    #     offset_coords = []
        
    #     for offset in self.compute_checkable_offsets(decision):
    #         offset_coords.append((decision[0] + offset[0], decision[1] + offset[1]))

    #     valid_coords = list(set(valid_coords) & set(offset_coords))
    #     print(valid_coords)
    #     decision = choice(valid_coords)
    #     print(decision)

    #     # Get resulting board
    #     if board[decision[0]][decision[1]] == Cell.WATER:
    #         board[decision[0]][decision[1]] = Cell.MISS

    #     if self.check_ship(decision, board):
    #         board[decision[0]][decision[1]] = Cell.FRESH_HIT

    #     return board

    # # Gets a list of all hits that havent sunk a ship
    # def get_all_hits(self, board, ship_positions):
    #     all_hits = []

    #     for i in range(5):
    #         for j in range(5):
    #             if board[i][j] in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP) and not self.check_destroyed_ship(board, ship_positions, (i, j)):
    #                 all_hits.append((i, j))

    #     return all_hits

    # # Gets a list of all valid coords that a move could be made based on the board and ship positions
    # def get_all_valid_coords(self, board, ship_positions):
    #     valid_coords = []
    #     for i in range(5):
    #         for j in range(5):
    #             # Check if cell is a hit or a miss already
    #             if board[i][j] in (Cell.HIT, Cell.MISS, Cell.FRESH_HIT):
    #                 continue

    #             # Check if cell is adjacent to a destroyed ship
    #             if self.adjacent_to_destroyed_ship(board, ship_positions, (i, j)):
    #                 continue

    #             valid_coords.append((i, j))

    #     return valid_coords

    # # Checks if a given cell is adjacent to a ship that has been destroyed
    # def adjacent_to_destroyed_ship(self, board, ship_positions, cell_coordinate):
    #     offsets = self.compute_checkable_offsets(cell_coordinate)

    #     for offset in offsets:
    #         offset_coord = (cell_coordinate[0]+offset[0], cell_coordinate[1]+offset[1])
    #         destroyed_ship = self.check_destroyed_ship(board, ship_positions, offset_coord)
            
    #         if destroyed_ship != 0:
    #             return True

    #     return False

    # # Checks if a cell is part of a destroyed ship
    # def check_destroyed_ship(self, board, ship_positions, cell_coordinate):
    #     # Not a destroyed ship if the checked cell isn't a hit
    #     if not self.get_cell(board, cell_coordinate) in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP):
    #         return 0
        
    #     # Check if 1 long
    #     if list(cell_coordinate) == ship_positions["1"][0]:
    #         return Cell.SMALL_SHIP
        
    #     # Check if its 2 long
    #     if list(cell_coordinate) in ship_positions["2"]:
    #         if self.get_cell(board, ship_positions["2"][0]) in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP) and self.get_cell(board, ship_positions["2"][1]) in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP):
    #             return Cell.MEDIUM_SHIP
            
    #     # Check if its 3 long
    #     if list(cell_coordinate) in ship_positions["3"]:
    #         if self.get_cell(board, ship_positions["3"][0]) in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP) and self.get_cell(board, ship_positions["3"][1]) in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP) and self.get_cell(board, ship_positions["3"][2]) in (Cell.HIT, Cell.FRESH_HIT, Cell.SUNKEN_SHIP):
    #             return Cell.LARGE_SHIP
            
    #     return 0

    # # Gets a dict of ship positions
    # def get_ship_positions(self, ship_matrix):
    #     ship_positions = {1: [], 2: [], 3: []}
    #     for i in range(5):
    #         for j in range(5):
    #             if self.get_cell(ship_matrix, coord := (i, j)) == Cell.SMALL_SHIP:
    #                 ship_positions[1].append(coord)
    #                 continue

    #             if self.get_cell(ship_matrix, coord := (i, j)) == Cell.MEDIUM_SHIP:
    #                 ship_positions[2].append(coord)
    #                 continue

    #             if self.get_cell(ship_matrix, coord := (i, j)) == Cell.LARGE_SHIP:
    #                 ship_positions[3].append(coord)
    #                 continue

    #     return ship_positions

    # # Gets the value of a cell
    # def get_cell(self, ship_matrix, cell_coordinate):
    #     return ship_matrix[cell_coordinate[0]][cell_coordinate[1]]

    # Checks if a coordinate contains a ship
    def check_ship(self, coord, board):
        return board[coord[0]][coord[1]] in (Board.SMALL_SHIP, Board.MEDIUM_SHIP, Board.LARGE_SHIP)
    
    # Generate buttons for minsweeper board
    def generate_buttons(self, user, disable_all = False):
        buttons = []
        started = ButtonStyle.GRAY if self.game_begun(board, revealed) else ButtonStyle.GREEN

        for i in range(5):
            row = []
            for j in range(5):
                cell = board[i][j]
                revealed_cell = revealed[i][j]

                if cell == Board.SMALL_SHIP:
                    row.append(Button(style=started, emoji="⛵", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if cell == Board.MEDIUM_SHIP:
                    row.append(Button(style=started, emoji="🚢", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if cell == Board.LARGE_SHIP:
                    row.append(Button(style=started, emoji="🛳️", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if revealed_cell == Revealed.MISS:
                    row.append(Button(style=ButtonStyle.BLUE, emoji="💦", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if revealed_cell == Revealed.HIT:
                    row.append(Button(style=ButtonStyle.RED, emoji="🔥", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if revealed_cell == Revealed.FRESH_HIT:
                    row.append(Button(style=ButtonStyle.RED, emoji="💥", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if revealed_cell == Revealed.SUNKEN_SHIP:
                    row.append(Button(style=ButtonStyle.RED, emoji="☠️", custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                if randint(1, 6) == 1:
                    row.append(Button(style=ButtonStyle.BLUE, emoji=choice(("🐳", "🐬", "🦭", "🐟", "🐠", "🐡", "🦈", "🐙", "🐚", "🐋", "🦑")), custom_id=f"battleship_{i}{j}", disabled=disable_all))
                    continue

                row.append(Button(style=ButtonStyle.BLUE, label="‎", custom_id=f"battleship_{i}{j}", disabled=disable_all))

            buttons.append(row)

        return buttons

    # # Based on the cell location returns the offsets from it that within the board
    # def compute_checkable_offsets(self, cell_coordinate):
    #     offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    #     # Remove impossible offsets
    #     if cell_coordinate[0] == 0:
    #         # Cant check cells above
    #         remove_offsets = [(-1, -1), (-1, 0), (-1, 1)]
    #         for offset in remove_offsets:
    #             try:
    #                 offsets.remove(offset)
    #             except:
    #                 pass

    #     if cell_coordinate[0] == 4:
    #         # Cant check cells below
    #         remove_offsets = [(1, -1), (1, 0), (1, 1)]
    #         for offset in remove_offsets:
    #             try:
    #                 offsets.remove(offset)
    #             except:
    #                 pass

    #     if cell_coordinate[1] == 0:
    #         # Cant check cells to the left
    #         remove_offsets = [(-1, -1), (0, -1), (1, -1)]
    #         for offset in remove_offsets:
    #             try:
    #                 offsets.remove(offset)
    #             except:
    #                 pass

    #     if cell_coordinate[1] == 4:
    #         # Cant check cells to the right
    #         remove_offsets = [(-1, 1), (0, 1), (1, 1)]
    #         for offset in remove_offsets:
    #             try:
    #                 offsets.remove(offset)
    #             except:
    #                 pass
        
    #     return offsets

class BattleshipPlayer:
    def __init__(self) -> None:
        self.board = self.generate_random_board()
        self.bot_board = self.generate_random_board()
        self.started = False
        self.turn = choice("bot", "user")
        self.revealed = self.empty_board()
        self.bot_revealed = self.empty_board()
        self.message = None

    def empty_board(self):
        return [[0] * 5 for _ in range(5)]

    # Generates a board with random ship layout
    def generate_random_board(self):
        # Initialize board
        board = self.empty_board()

        # Define ship lengths
        ship_lengths = [3, 2, 1]

        # Place ships randomly on the board
        for length in ship_lengths:
            while True:
                # Randomly choose a starting position and orientation for the ship
                row = randint(0, 4)
                col = randint(0, 4)
                orientation = choice(['horizontal', 'vertical'])

                # Check if the ship fits in the chosen position and orientation
                if orientation == 'horizontal' and col + length <= 5:
                    valid = True
                    for i in range(length):
                        if not self.is_valid_ship_placement(row, col + i, board):
                            valid = False
                            break
                    if valid:
                        for i in range(length):
                            board[row][col + i] = length
                        break

                elif orientation == 'vertical' and row + length <= 5:
                    valid = True
                    for i in range(length):
                        if not self.is_valid_ship_placement(row + i, col, board):
                            valid = False
                            break
                    if valid:
                        for i in range(length):
                            board[row + i][col] = length
                        break

        return board

    # Checks if a position is valid for ship placement
    def is_valid_ship_placement(self, row, col, board):
        # Check if the position is out of bounds
        if row < 0 or row >= 5 or col < 0 or col >= 5:
            return False

        # Check if the position or its adjacent positions already have a ship
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                if r >= 0 and r < 5 and c >= 0 and c < 5 and board[r][c] != 0:
                    return False

        return True

class Board:
    WATER = 0
    SMALL_SHIP = 1
    MEDIUM_SHIP = 2
    LARGE_SHIP = 3

class Revealed:
    NO = 0
    MISS = 1
    HIT = 2
    FRESH_HIT = 3
    SUNKEN_SHIP = 4

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Battleship(bot)