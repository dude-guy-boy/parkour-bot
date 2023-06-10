# faq.py

from interactions import (
    Client,
    Extension,
    slash_command,
    slash_option,
    SlashContext,
    OptionType,
    Embed,
    AutocompleteContext
    )
import src.logs as logs
from lookups.colors import Color
from src.database import Data

class FAQ(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### /FAQ ###
    @slash_command(
        name="faq",
        description="Get answers for frequently asked questions!",
    )
    @slash_option(
        name="question",
        description="The question you would like to ask",
        required=True,
        opt_type=OptionType.STRING,
        autocomplete=True
    )
    async def faq_command(self, ctx: SlashContext, question: str):
        try:
            question, answer = Data.get_item_from_start(table="faq", key_start=question)
        except:
            await ctx.send(embed=Embed(description="Sorry, that question doesn't exist!", color=Color.RED))
            return

        await ctx.send(embed=Embed(title=question, description=answer, color=Color.GREEN))

    ### /FAQ-ADD ###
    @slash_command(
        name="faq-add",
        description="Add a question and answer to the faq list"
    )
    @slash_option(
        name="question",
        description="The question",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="answer",
        description="The answer to the question",
        required=True,
        opt_type=OptionType.STRING
    )
    async def faq_add_command(self, ctx: SlashContext, question: str, answer: str):
        Data.set_data_item(table="faq", key=question, value=answer)
        await ctx.send(embed=Embed(description=f"Added FAQ `{question}` with answer `{answer}`.", color=Color.GREEN))

    ### /FAQ-REMOVE ###
    @slash_command(
        name="faq-remove",
        description="Remove a question from the faq list"
    )
    @slash_option(
        name="question",
        description="The question",
        required=True,
        opt_type=OptionType.STRING,
        autocomplete=True
    )
    async def faq_remove_command(self, ctx: SlashContext, question: str):
        try:
            key, value = Data.get_item_from_start(table="faq", key_start=question)
        except:
            await ctx.send(embed=Embed(description="Sorry, that question doesn't exist!", color=Color.RED))
            return
        
        Data.delete_item(table="faq", item={'key': key, 'value': value})
        await ctx.send(embed=Embed(description=f"Removed FAQ Q:`{key}` A:`{value}`", color=Color.GREEN))

    ### FAQ question autocomplete ###
    @faq_command.autocomplete("question")
    @faq_remove_command.autocomplete("question")
    async def faq_question_autocomplete(self, ctx: AutocompleteContext):
        faqs = Data.get_all_items("faq")
        choices = []

        for idx, item in enumerate(faqs):
            if item['key'].startswith(ctx.input_text):
                choices.append({"name": item['key'][:80], "value": item['key'][:100]})
        
        await ctx.send(choices=choices[:25])

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    FAQ(bot)