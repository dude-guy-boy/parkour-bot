# 2048.py

from interactions import (
    MISSING,
    Client,
    ComponentContext,
    Extension,
    Embed,
    ButtonStyle,
    Button,
    Modal,
    ShortText,
    listen,
    modal_callback
    )
from interactions.ext.hybrid_commands import hybrid_slash_command, HybridContext
from interactions.api.events.internal import Component
import src.logs as logs
from lookups.colors import Color
from src.database import UserData
from random import randint, choices

class Twenty48(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### /2048 ###
    @hybrid_slash_command(
        name="2048",
        description="Play a game of 2048!"
    )
    async def twenty_48(self, ctx: HybridContext):
        # Defer if slash command
        if ctx.prefix == "/":
            await ctx.defer()

        # Create empty board
        board = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

        # Fill two random tiles
        board, _ = self.add_new_tile(board)
        board, _ = self.add_new_tile(board)

        # Get the user
        user = UserData.get_user(ctx.author.id)

        # If the user doesn't exist, initialise their 2048 data
        if not user:
            user = {"board": board, "score": 0, "high_score": 0, "largest_number": 0,
                    "games_played": 0, "cumulative_score": 0, "message": None}

        # If the user already has a game running, delete the old message and send it again
        if user:
            if user["message"]:
                old_channel = await self.bot.fetch_channel(user["message"]['channel_id'])
                old_message = await old_channel.fetch_message(user["message"]['message_id'])
                await old_message.delete()

                embed = Embed(
                    description=f"{ctx.author.mention} here's your existing game of 2048!\nHigh Score: `{user['high_score']}`\nCurrent Score: `{user['score']}`",
                    color=Color.GREEN
                )

                new_message = await ctx.send(embed=embed, components=self.generate_buttons(user["board"]))

                # Update the message
                user["message"] = {"message_id": int(
                    new_message.id), "channel_id": int(new_message.channel.id)}
                
                UserData.set_user(ctx.author.id, user)
                return

        # Generate buttons and send the game
        embed = Embed(
            description=f"{ctx.author.mention} here's your game of 2048!\nHigh Score: `{user['high_score']}`\nCurrent Score: `0`",
            color=Color.GREEN
        )

        game = await ctx.send(embed=embed, components=self.generate_buttons(board))

        # Update fields
        user["message"] = {"message_id": int(
            game.id), "channel_id": int(game.channel.id)}
        user["board"] = board
        user["games_played"] += 1

        UserData.set_user(ctx.author.id, user)

    ### On 2048 Button Press ###
    @listen("on_component")
    async def twenty_48_listener(self, component: Component):
        # Ignore non 2048 buttons
        if not component.ctx.custom_id.startswith("2048"):
            return
        
        # Get 2048 user
        user = UserData.get_user(component.ctx.author.id)

        custom_id = component.ctx.custom_id

        # Check if button presser is the game owner
        if not user or user["message"]["message_id"] != int(component.ctx.message.id):
            await component.ctx.send(embeds=Embed(description="That isn't your 2048 game!", color=Color.RED), ephemeral=True)
            return

        # End button pressed, send confirmation modal
        if(custom_id.endswith("end")):
            end_game_modal = Modal(
                ShortText(label="Enter 'end' to end the game:", custom_id="text_input_response"),
                title="End 2048 Game?",
                custom_id="end_game_modal"
            )

            await component.ctx.send_modal(end_game_modal)
            return

        board = user["board"]
        old_board = user["board"]

        additional_score = 0
        new_tile_coordinate = []

        # Left
        if(custom_id.endswith("left")):
            board, additional_score = self.left(board)

        # Right
        if(custom_id.endswith("right")):
            board, additional_score = self.right(board)

        # Up
        if(custom_id.endswith("up")):
            board, additional_score = self.up(board)

        # Down
        if(custom_id.endswith("down")):
            board, additional_score = self.down(board)

        # Only add new tile if move was valid
        if(board != old_board):
            board, new_tile_coordinate = self.add_new_tile(board)
        
        # Update board and score
        user["board"] = board
        user["score"] += additional_score
        if(user["score"] > user["high_score"]):
            user["high_score"] = user["score"]

        largest_tile = 0

        if(board):
            largest_tile = self.largest_tile_on_board(board)

        if(largest_tile > user["largest_number"]):
            user["largest_number"] = largest_tile

        # If no possible moves remain, end the game
        if(not self.any_possible_move(board)):
            await self.end_game(component.ctx, board, user, new_tile_coordinate)
            return

        embed = Embed(
            description=f"{component.ctx.author.mention} here's your game of 2048!\nHigh Score: `{user['high_score']}`\nCurrent Score: `{user['score']}`", color=Color.GREEN)

        await component.ctx.edit_origin(embed=embed, components=self.generate_buttons(board, new_tile=new_tile_coordinate))
        UserData.set_user(component.ctx.author.id, user)

    ### End Game Modal Callback ###
    @modal_callback("end_game_modal")
    async def end_game_modal_callback(self, ctx: ComponentContext, text_input_response: str):
        if(text_input_response.lower() == "end"):
            user = UserData.get_user(ctx.author.id)

            await ctx.send(embeds=Embed(description="Ended the game.", color=Color.GREEN), ephemeral=True)
            channel = await self.bot.fetch_channel(user["message"]['channel_id'])
            message = await channel.fetch_message(user["message"]['message_id'])
            await self.end_game(ctx, user["board"], user, message=message)
        else:
            await ctx.send(embeds = Embed(description="You didn't end the game.", color=Color.RED), ephemeral = True)

    # Ends the game
    async def end_game(self, ctx, board, user, new_tile_coordinate = None, message = None):
        embed = Embed(
            description=f"Game Over {ctx.author.mention}!\nScore: `{user['score']}`", color=Color.RED)

        # Clear user score, message & board, add to cumulative score
        user["cumulative_score"] += user["score"]
        user["score"] = 0
        user["message"] = None
        user["board"] = None

        UserData.set_user(ctx.author.id, user)

        if(message):
            ctx = message

        await ctx.edit(embeds=embed, components=self.generate_buttons(board, new_tile=new_tile_coordinate, game_over=True))

    # Gets the largest tile on the board
    def largest_tile_on_board(self, board):
        largest_tile = 0
        for i in range(4):
            for j in range(4):
                if(board[i][j] > largest_tile):
                    largest_tile = board[i][j]
        return largest_tile

    # Checks if any move is possible
    def any_possible_move(self, board):
        old_board = board

        board_1, _ = self.left(board)
        board_2, _ = self.right(board)
        board_3, _ = self.up(board)
        board_4, _ = self.down(board)

        if(board_1 == old_board and board_2 == old_board and board_3 == old_board and board_4 == old_board):
            return False
        else:
            return True

    # Left move
    def left(self, board):
        board = self.stack(board)
        board, additional_score = self.combine(board)
        board = self.stack(board)
        return board, additional_score

    # Right move
    def right(self, board):
        board = self.reverse(board)
        board = self.stack(board)
        board, additional_score = self.combine(board)
        board = self.stack(board)
        board = self.reverse(board)
        return board, additional_score

    # Upwards move
    def up(self, board):
        board = self.transpose(board)
        board = self.stack(board)
        board, additional_score = self.combine(board)
        board = self.stack(board)
        board = self.transpose(board)
        return board, additional_score

    # Downwards move
    def down(self, board):
        board = self.transpose(board)
        board = self.reverse(board)
        board = self.stack(board)
        board, additional_score = self.combine(board)
        board = self.stack(board)
        board = self.reverse(board)
        board = self.transpose(board)
        return board, additional_score

    def stack(self, board):
        new_matrix = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        for i in range(4):
            fill_position = 0
            for j in range(4):
                if(board[i][j] != 0):
                    new_matrix[i][fill_position] = board[i][j]
                    fill_position += 1
        
        return new_matrix
    
    def combine(self, board):
        score = 0
        for i in range(4):
            for j in range(3):
                if(board[i][j] != 0 and board[i][j] == board[i][j+1]):
                    board[i][j] *= 2
                    board[i][j+1] = 0
                    score += board[i][j]
        
        return board, score

    def reverse(self, board):
        new_matrix = []
        for i in range(4):
            new_matrix.append([])
            for j in range(4):
                new_matrix[i].append(board[i][3-j])
        return new_matrix

    def transpose(self, board):
        new_matrix = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        for i in range(4):
            for j in range(4):
                new_matrix[i][j] = board[j][i]
        return new_matrix

    def add_new_tile(self, board):
        row = randint(0, 3)
        col = randint(0, 3)
        while(board[row][col] != 0):
            row = randint(0, 3)
            col = randint(0, 3)
        board[row][col] = choices(population=[2, 4], weights=[0.9,0.1])[0]

        return board, (row, col)

    def generate_buttons(self, board, new_tile = None, game_over = False):
        buttons = []
        for i in range(4):
            row = []
            for j in range(4):
                # Tile is empty
                if(board[i][j] == 0):
                    row.append(Button(
                        style=ButtonStyle.SECONDARY,
                        label="‎",
                        custom_id=f"2048_{i}{j}")
                    )
                    continue

                # Tile is not empty
                row.append(Button(
                    style=ButtonStyle.PRIMARY if (i, j) != new_tile else ButtonStyle.SUCCESS,
                    label=str(board[i][j]),
                    custom_id=f"2048_{i}{j}",
                    disabled=game_over)
                )

            buttons.append(row)

        # Directional control buttons
        buttons.append([
            Button(style=ButtonStyle.SUCCESS, label="←", custom_id="2048_left", disabled=game_over),
            Button(style=ButtonStyle.SUCCESS, label="↑", custom_id="2048_up", disabled=game_over),
            Button(style=ButtonStyle.SUCCESS, label="↓", custom_id="2048_down", disabled=game_over),
            Button(style=ButtonStyle.SUCCESS, label="→", custom_id="2048_right", disabled=game_over),
            Button(style=ButtonStyle.DANGER, label="End Game", custom_id="2048_end", disabled=game_over),
        ])

        return buttons

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Twenty48(bot)