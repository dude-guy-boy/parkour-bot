# todo.py

from interactions import (
    Client,
    Extension,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    ButtonStyle,
    AutocompleteContext
    )
from src.custompaginator import Paginator
import src.logs as logs
from lookups.colors import Color
from src.database import UserData

class Todo(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### /TODO ADD ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="add",
        sub_cmd_description="Add a task to your todo list",
    )
    @slash_option(
        name="task",
        description="What you would like to add to your todo list",
        required=True,
        opt_type=OptionType.STRING
    )
    async def todo_add(self, ctx: SlashContext, task):        
        # If user is not in todo db, add them
        todo_list = UserData.get_user(id=ctx.user.id, table="todo")

        # If task already on their list, say so
        for item in todo_list:
            if item.casefold() == task.casefold():
                await ctx.send(embed=Embed(description = f"You already have `{task}` on your todo list!", color = Color.RED))
                return

        todo_list.append(task)
        UserData.set_user(id=ctx.user.id, data=todo_list, table="todo")

        await ctx.send(embed=Embed(description=f"Added `{task}` to your todo list.", color=Color.GREEN))

    ### /TODO REMOVE ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="remove",
        sub_cmd_description="Remove a task from your todo list without marking it as done"
    )
    @slash_option(
        name="task",
        description="The task you would like to remove from your todo list",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True
    )
    async def todo_remove(self, ctx: SlashContext, task):
        todo_list = UserData.get_user(id=ctx.user.id, table="todo")

        # If item not on their list, say so
        try:
            todo_list.remove(task)
        except:
            await ctx.send(embed=Embed(description = f"`{task}` is not on your todo list!", color = Color.RED))
            return
        
        UserData.set_user(id=ctx.user.id, data=todo_list, table="todo")
        await ctx.send(embed=Embed(description=f"Removed `{task}` from your todo list.", color=Color.GREEN))

    ### /TODO LIST ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="list",
        sub_cmd_description="View your todo list",
    )
    async def todo_list(self, ctx: SlashContext):
        todo_list = UserData.get_user(id=ctx.user.id, table="todo")
        
        if not todo_list:
            await ctx.send(embed=Embed(description="Your todo list is empty!\nTo add something to it use: `/todo add <text>`", color=Color.RED))
            return
        
        formatted_list = []

        for idx, item in enumerate(todo_list):
            formatted_list.append(f"{(idx+1):02}: {item}")

        paginator = Paginator.create_from_string(
            self.bot,
            "\n".join(formatted_list),
            num_lines=10,
            page_size=1000,
            prefix="```",
            suffix="```",
            allow_multi_user=True
            )
        paginator.default_button_color = ButtonStyle.GRAY
        paginator.default_color = Color.GREEN
        paginator.default_title = "Your Todo List"

        await paginator.send(ctx)

    ### /TODO COMPLETED ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="completed",
        sub_cmd_description="View a list of all your completed tasks",
    )
    async def todo_completed(self, ctx: SlashContext):
        done_list = UserData.get_user(id=ctx.user.id, table="done")
        
        if not done_list:
            await ctx.send(embed=Embed(description="Your completed task list is empty!\nTo add something to it mark a task from your todo list as done, using: `/todo done <item>`", color=Color.RED))
            return
        
        done_list.reverse()
        formatted_list = []

        for idx, item in enumerate(done_list):
            formatted_list.append(f"{(len(done_list)-(idx)):02}: {item}")

        paginator = Paginator.create_from_string(
            self.bot,
            "\n".join(formatted_list),
            num_lines=10,
            page_size=1000,
            prefix="```",
            suffix="```",
            allow_multi_user=True
            )
        paginator.default_button_color = ButtonStyle.GRAY
        paginator.default_color = Color.GREEN
        paginator.default_title = "Your Completed Tasks"

        await paginator.send(ctx)

    ### /TODO DONE ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="done",
        sub_cmd_description="Mark something on your todo list as done",
    )
    @slash_option(
        name = "task",
        description = "The task on your todo list you want to mark as done",
        required = True,
        opt_type = OptionType.STRING,
        autocomplete = True
    )
    async def todo_done(self, ctx: SlashContext, task):
        todo_list = UserData.get_user(id=ctx.user.id, table="todo")
        done_list = UserData.get_user(id=ctx.user.id, table="done")
        
        # For tasks longer than 100 chars because
        # max length for autocomplete value is 100
        for item in todo_list:
            if len(task) == 100 and item.startswith(task):
                task = item

        try:
            # Remove task
            todo_list.remove(task)
        except:
            await ctx.send(embed=Embed(description=f"Task `{task}` is not on your todo list.", color=Color.RED))
            return
        
        # Set new list
        UserData.set_user(id=ctx.user.id, data=todo_list, table="todo")

        # Add task to done list
        done_list.append(task)
        UserData.set_user(id=ctx.user.id, data=done_list, table="done")

        await ctx.send(embed=Embed(description = f"Marked task: `{task}` as done.", color=Color.GREEN))

    ### /TODO CLEAR ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="clear",
        sub_cmd_description="Mark everything on your todo list as done",
    )
    async def todo_clear(self, ctx: SlashContext):
        todo_list = UserData.get_user(id=ctx.user.id, table="todo")
        done_list = UserData.get_user(id=ctx.user.id, table="done")

        # Add all to done list
        done_list.extend(todo_list)

        UserData.set_user(id=ctx.user.id, data=[], table="todo")
        UserData.set_user(id=ctx.user.id, data=done_list, table="done")
        await ctx.send(embed=Embed(description = f"Cleared your todo list!", color=Color.GREEN))

    ### Task autocomplete ###
    @todo_done.autocomplete("task")
    @todo_remove.autocomplete("task")
    async def todo_task_autocomplete(self, ctx: AutocompleteContext):
        todo_list = UserData.get_user(id=ctx.user.id, table="todo")
        choices = []

        for idx, task in enumerate(todo_list):
            if task.startswith(ctx.input_text):
                choices.append({"name": f"{(idx+1):02}: {task[:80]}", "value": task[:100]})
        
        await ctx.send(choices=choices[:25])

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Todo(bot)