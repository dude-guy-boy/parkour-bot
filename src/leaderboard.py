# leaderboard.py

from typing import List, Optional, Union
from interactions import (
    BaseContext,
    Embed,
    Message,
    SlashContext,
    ButtonStyle,
    EmbedField
)
from lookups.colors import Color
from src.custompaginator import Paginator

class Leaderboard(Paginator):
    @classmethod
    def create(cls, client, data: List[dict], field_map: dict, sort_by: str, descending: bool = True, secondary_sort_by: str = None, secondary_descending: bool = True, embed_color = Color.GREEN, button_style = ButtonStyle.GRAY, title: str = None, text: str = None, page_len: int = 10, use_medals: bool = True) -> Paginator:
        """
        Creates a leaderboard paginator

        Args:
            client: A reference to the client
            data: The leaderboard data, unsorted. List of dicts [{"user": user_id, "wins": num_wins}, ...]
            field_map: Dict of field names and the value if data they reference eg. {"Leaderboard": "user", "Wins": "wins"}. The first field will have the rank numbers applied to it
            sort_by: Name of the field the leaderboard should be sorted by
            descending: If the order should be large -> small
            secondary_sort_by: Name of the field the leaderboard should secondarily be sorted by
            secondary_descending: If the secondary order should be large -> small
            embed_color: Color of the embeds
            button_style: Style of buttons
            title: The title of all pages
            text: The embed description for all pages
            page_len: The number of leaderboard entries that should be on each page
            use_medals: Whether the top 3 should be labelled using medal emojis. If false uses #1, #2, #3

        Returns:
            A leaderboard paginator
        """

        # Check that field map matches data
        for field in field_map:
            if field_map[field] not in data[0]:
                raise AttributeError(f"Data '{field_map[field]}' for field '{field}' is not in the provided data")
        
        # Check that sort_by is an existing field
        if sort_by not in data[0]:
            raise AttributeError(f"The sorting field specified '{sort_by}' is not in the provided data")
        
        # If secondary_sort_by is also provided, check that it exists
        if secondary_sort_by:
            if secondary_sort_by not in data[0]:
                raise AttributeError(f"The secondary sorting field specified '{secondary_sort_by}' is not in the provided data")

        # Sort data
        sorted_data = None
        if secondary_sort_by:
            sorted_data = sorted(data, key=lambda x: ((-x[sort_by] if descending else x[sort_by]), (-x[secondary_sort_by] if secondary_descending else x[secondary_sort_by])))
        else:
            sorted_data = sorted(data, key=lambda x: -x[sort_by] if descending else x[sort_by])

        # Split data into pages
        paginated_data = [sorted_data[i:i+page_len] for i in range(0, len(sorted_data), page_len)]

        embeds = []

        for page_index, page in enumerate(paginated_data):
            fields = {}
            for field in field_map:
                fields[field] = []

            # Get the lists for each field
            for entry in page:
                for field in field_map:
                    field_name = field_map[field]

                    fields[field].append(entry[field_name])

            # Add rank numbers to first field in field_map
            ranked_field = []
            for value_index, value in enumerate(fields[next(iter(fields))]):
                rank = page_index * page_len + value_index + 1

                if use_medals:
                    if rank == 1:
                        rank = "🥇"
                    if rank == 2:
                        rank = "🥈"
                    if rank == 3:
                        rank = "🥉"
                else:
                    rank = f"#{rank}"

                ranked_field.append(f"{rank} {value}")

            fields[next(iter(fields))] = ranked_field

            # Turn fields into list of EmbedField objects
            embed_fields = []
            for field in fields:
                embed_fields.append(
                    EmbedField(
                        name=field,
                        value="\n".join([str(thing) for thing in fields[field]]),
                        inline=True
                    )
                )

            # Make embed
            embeds.append(
                Embed(
                    title=title,
                    description=text,
                    fields=embed_fields
                )
            )

        # Create paginator
        paginator = cls.create_from_embeds(client, *embeds)
        paginator.default_color = embed_color
        paginator.default_button_color = button_style

        # Return paginator
        return paginator
    
    async def send(self, ctx: Optional[Union[BaseContext, SlashContext]] = None, channel_id: Optional[int] = None, ephemeral: bool = False, author_id: Optional[int] = None) -> Message:
        await super().send(ctx, channel_id=channel_id, ephemeral=ephemeral, author_id=author_id)