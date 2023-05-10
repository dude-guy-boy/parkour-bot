# template.py

### This is a template extension ###

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
import src.logs as logs
from src.colors import Color
from src.database import Data

class Dictionary(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()

    ### /DEFINE ###
    @slash_command(
        name="define",
        description="Search the parkour dictionary!"
    )
    @slash_option(
        name="entry",
        description="The dictionary entry you would like the definition for",
        required=True,
        opt_type=OptionType.STRING,
        autocomplete=True
    )
    async def define_command(self, ctx: SlashContext, entry: str):
        try:
            definition = Data.get_data_item(table="dictionary", key=entry)['definition']
        except:
            await ctx.send(embed=Embed(description="Sorry, that entry doesn't exist!", color=Color.RED))
            return
        
        other_defined_terms = []

        dictionary = Data.get_all_items(table="dictionary")
        print(f"Dictionary: {dictionary}")
        for item in dictionary:
            # Add all defined dictionary entries to a list
            if (pos := definition.find(item['key'])) != -1:
                other_defined_terms.append({'term': item['key'], 'pos': pos})

            # Do the same for all aliases
            try:
                for alias in item['value']['aliases']:
                    if (pos := definition.find(alias)) != -1:
                        other_defined_terms.append({'term': alias, 'pos': pos})
            except TypeError:
                # When aliases list is None
                pass

        # Check if any are inside others
        terms_copy = other_defined_terms

        for terms_1 in other_defined_terms:
            for terms_2 in other_defined_terms:
                # If the term is inside the first one
                if terms_2['pos'] > terms_1['pos'] and terms_2['pos'] < terms_1['pos'] + len(terms_1['term']):
                    try:
                        terms_copy.remove(terms_2)
                    except:
                        pass

        # Reverse order so that the underline markdown chars can be added without worrying about
        # shifting the position to account for the added chars.
        sorted_defined_terms = sorted(terms_copy, key=lambda d: d['pos'], reverse=True)

        # Underline other searchable terms
        formatted_definition = definition
        for term in sorted_defined_terms:
            # Add underline markdown chars
            formatted_definition = formatted_definition[:term['pos'] + len(term['term'])] + "__" + formatted_definition[term['pos'] + len(term['term']):]
            formatted_definition = formatted_definition[:term['pos']] + "__" + formatted_definition[term['pos']:]
        
        definition_embed = Embed(
            title=entry,
            description=formatted_definition,
            color=Color.GREEN,
            footer="Underlined words are also in the dictionary!"
        )

        await ctx.send(embed=definition_embed)

    ### /DICTIONARY-ADD ###
    @slash_command(
        name="definition-add",
        description="Add a new entry to the dictionary"
    )
    @slash_option(
        name="entry",
        description="The entry you would like to add",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="definition",
        description="The definition of the entry",
        required=True,
        opt_type=OptionType.STRING
    )
    @slash_option(
        name="aliases",
        description="A list of aliases for the entry, separated by commas",
        required=False,
        opt_type=OptionType.STRING
    )
    async def definition_add_command(self, ctx: SlashContext, entry: str,  definition: str, aliases: str = None):
        try:
            aliases = [alias.strip() for alias in aliases.split(",")]
        except:
            pass

        Data.set_data_item(table="dictionary", key=entry, value={"aliases": aliases, "definition": definition})
        
        if type(aliases) == list:
            aliases = ', '.join(aliases)

        await ctx.send(embed=Embed(description=f"Added `{entry}` {('('+aliases+')') if aliases else ''} to the dictionary with definition `{definition}`.", color=Color.GREEN))

    @slash_command(
        name="definition-remove",
        description="Remove an entry from the dictionary"
    )
    @slash_option(
        name="entry",
        description="The entry you would like to remove",
        opt_type=OptionType.STRING,
        required=True,
        autocomplete=True
    )
    async def definition_remove_command(self, ctx: SlashContext, entry: str):
        try:
            definition = Data.get_data_item(table="dictionary", key=entry)
        except:
            await ctx.send(embed=Embed(description="Sorry, that entry doesn't exist!", color=Color.RED))
            return
        
        Data.delete_item(table="dictionary", item={'key': entry, 'value': definition})
        await ctx.send(embed=Embed(description=f"Removed definition for `{entry}` from the dictionary", color=Color.GREEN))

    ### Dictionary entry autocomplete ###
    @define_command.autocomplete("entry")
    @definition_remove_command.autocomplete("entry")
    async def faq_question_autocomplete(self, ctx: AutocompleteContext):
        entries = Data.get_all_items("dictionary")
        print(f"Entries: {entries}")
        choices = []

        for item in entries:
            if item['value']['aliases']:
                for alias in item['value']['aliases']:
                    if alias.startswith(ctx.input_text):
                        choices.append({"name": alias[:80], "value": item['key'][:100]})

            if item['key'].startswith(ctx.input_text):
                choices.append({"name": item['key'][:80], "value": item['key'][:100]})
        
        await ctx.send(choices=choices[:25])

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    Dictionary(bot)