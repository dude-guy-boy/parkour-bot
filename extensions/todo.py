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
from interactions.ext.paginators import Paginator
import src.logs as logs
import os.path as path
import src.colors as color
from tinydb import TinyDB, Query

class Todo(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()
        self.users = TinyDB(f"./data/{path.basename(__file__)[:-3]}.json").table("users")
        self.user = Query()

    def init_user(self, id):
        '''Adds user to todo database if they are not already there'''
        # If user is not in todo db, add them
        if not self.users.search(self.user.id == int(id)):
            self.users.insert({"id": int(id), "todo_list": [], "done_list": []})

    def get_todo_list(self, id) -> list:
        '''Returns the users todo list'''
        
        # Ensure user is in db
        self.init_user(id)
        
        # Return their todo list
        return self.users.search(self.user.id == int(id))[0]['todo_list']

    def set_todo_list(self, todo_list: list, id):
        '''Sets the users todo list to the provided list'''

        self.users.update({"todo_list": todo_list}, self.user.id == int(id))

    def get_done_list(self, id) -> list:
        '''Returns the users done list'''
        
        # Ensure user is in db
        self.init_user(id)
        
        # Return their done list
        return self.users.search(self.user.id == int(id))[0]['done_list']

    def set_done_list(self, done_list: list, id):
        '''Sets the users done list to the provided list'''

        self.users.update({"done_list": done_list}, self.user.id == int(id))

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
        todo_list = self.get_todo_list(ctx.user.id)

        # If task already on their list, say so
        for item in todo_list:
            if item.casefold() == task.casefold():
                await ctx.send(embed=Embed(description = f"You already have `{task}` on your todo list!", color = color.RED))
                return

        todo_list.append(task)
        self.set_todo_list(todo_list, ctx.user.id)

        await ctx.send(embed=Embed(description=f"Added `{task}` to your todo list.", color=color.GREEN))

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
        todo_list = self.get_todo_list(ctx.user.id)

        # If item not on their list, say so
        try:
            todo_list.remove(task)
        except:
            await ctx.send(embed=Embed(description = f"`{task}` is not on your todo list!", color = color.RED))
            return
        
        self.set_todo_list(todo_list, ctx.user.id)
        await ctx.send(embed=Embed(description=f"Removed `{task}` from your todo list.", color=color.GREEN))

    ### /TODO LIST ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="list",
        sub_cmd_description="View your todo list",
    )
    async def todo_list_todo(self, ctx: SlashContext):
        todo_list = self.get_todo_list(ctx.user.id)
        
        if not todo_list:
            await ctx.send(embed=Embed(description="Your todo list is empty!\nTo add something to it use: `/todo add <text>`", color=color.RED))
            return
        
        formatted_list = []

        for idx, item in enumerate(todo_list):
            formatted_list.append(f"{(idx+1):02}: {item}")

        formatted_list = "```" + "\n".join(formatted_list) + "```"

        paginator = Paginator.create_from_string(self.bot, formatted_list, page_size=1000)
        paginator.default_button_color = ButtonStyle.GRAY
        paginator.default_color = color.GREEN
        paginator.default_title = "Your Todo List"
        # paginator.back_button_emoji = '<'

        await paginator.send(ctx)

        # await ctx.send(formatted_list)

    ### /TODO COMPLETED ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="completed",
        sub_cmd_description="View a list of all your completed tasks",
    )
    async def todo_completed(self, ctx: SlashContext):
        done_list = self.get_done_list(ctx.user.id)
        
        if not done_list:
            await ctx.send(embed=Embed(description="Your completed task list is empty!\nTo add something to it mark a task from your todo list as done, using: `/todo done <item>`", color=color.RED))
            return
        
        done_list.reverse()
        formatted_list = []

        for idx, item in enumerate(done_list):
            formatted_list.append(f"{(len(done_list)-(idx)):02}: {item}")

        formatted_list = "```" + "\n".join(formatted_list) + "```"

        paginator = Paginator.create_from_string(self.bot, formatted_list, page_size=1000)
        paginator.default_button_color = ButtonStyle.GRAY
        paginator.default_color = color.GREEN
        paginator.default_title = "Your Completed Tasks"
        # paginator.back_button_emoji = '<'

        await paginator.send(ctx)

        # await ctx.send(formatted_list)

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
        todo_list = self.get_todo_list(ctx.user.id)
        done_list = self.get_done_list(ctx.user.id)
        
        try:
            # Remove task
            todo_list.remove(task)
        except:
            await ctx.send(embed=Embed(description=f"Task `{task}` is not on your todo list.", color=color.RED))
            return
        
        # Set new list
        self.set_todo_list(todo_list=todo_list, id=ctx.user.id)

        # Add task to done list
        done_list.append(task)
        self.set_done_list(done_list=done_list, id=ctx.user.id)

        await ctx.send(embed=Embed(description = f"Marked task: `{task}` as done.", color=color.GREEN))

    ### /TODO CLEAR ###
    @slash_command(
        name="todo",
        description="Todo base",
        sub_cmd_name="clear",
        sub_cmd_description="Mark everything on your todo list as done",
    )
    async def todo_clear(self, ctx: SlashContext):
        todo_list = self.get_todo_list(ctx.user.id)
        done_list = self.get_done_list(ctx.user.id)

        # Add all to done list
        done_list.extend(todo_list)

        self.set_todo_list(todo_list=[], id=ctx.user.id)
        self.set_done_list(done_list=done_list, id=ctx.user.id)
        await ctx.send(embed=Embed(description = f"Cleared your todo list!", color=color.GREEN))

    ### Task autocomplete ###
    @todo_done.autocomplete("task")
    @todo_remove.autocomplete("task")
    async def todo_task_autocomplete(self, ctx: AutocompleteContext):
        todo_list = self.get_todo_list(ctx.user.id)
        choices = []

        for idx, task in enumerate(todo_list):
            if task.startswith(ctx.input_text):
                choices.append({"name": f"{(idx+1):02}: {task}", "value": task})
        
        await ctx.send(choices=choices[:25])

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Todo(bot)