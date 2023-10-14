# autosync.py

import os
from dotenv import load_dotenv
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
from lookups.colors import Color
from src.database import Config, Data
import requests

class AutoSync(Extension):
    def __init__(self, client: Client):
        self.client = client
        self.logger = logs.init_logger()
        
        load_dotenv()
        self.sync_token = os.environ.get("SYNC_TOKEN")
        self.hpk_host = os.environ.get("HPK_LINK")
        self.scoville_host = os.environ.get("SCOVILLE_LINK")
        self.linkcraft_host = os.environ.get("LINKCRAFT_LINK")

    @slash_command(
        name="force-sync",
        description="Forces a sync"
    )
    async def force_sync(self, ctx: SlashContext):
        await ctx.defer(ephemeral=True)

        self.sync_scoville_maps()
        self.sync_scoville_players()

        self.sync_hpk_maps()
        self.sync_hpk_players()

        await ctx.send(embed=Embed(description="Synced", color=Color.GREEN), ephemeral=True)
        await logs.DiscordLogger.log(self.bot, ctx, description="Force synced all players and maps")

    # TODO: everything
    # DO AT A LATER DATE, JUST FOCUS ON BASIC FUNCTIONALITY FOR NOW
    def sync_scoville_maps(self):
        page_json = {"pageLength": 1000, "page": 1}
        headers = {"Authorization": "Bearer " + self.sync_token}

        response = requests.post(url=f"http://{self.scoville_host}/api/v1/get-maps", json=page_json, headers=headers).json()
        self.scoville_course_map = {map['uuid']: map['name'] for map in response['maps']}

        Data.set_data_item(key="scoville_maps", value=response['maps'])

    def sync_scoville_players(self):
        player_list = self.get_all_verified_users()
        
        players_json = {"players": player_list}
        headers = {"Authorization": "Bearer " + self.sync_token}

        response = requests.post(url=f"http://{self.scoville_host}/api/v1/get-players/", json=players_json, headers=headers).json()
        
        if len(response['invalidPlayers']):
            self.logger.info(f"Could not sync the following scoville players: {', '.join(response['invalidPlayers'])}")

        for player in response['players']:
            translated_maps = self.translate_scoville_maps(player['completedMaps'])
            # print(translated_maps)
            # TODO: In future, check for each map existing in the added maps
            # Then only add the ones that exist to the player

    def sync_hpk_maps(self):
        page_json = {"pageLength": 1, "page": 1}
        headers = {"Authorization": "Bearer " + self.sync_token}

        for page in range(60):
            page_json = {"pageLength": 1, "page": page}
            response = requests.post(url=f"http://{self.hpk_host}/api/v1/get-maps", json=page_json, headers=headers).json()
            print(response)

        return

        response = requests.post(url=f"http://{self.hpk_host}/api/v1/get-maps", json=page_json, headers=headers).json()
        print(response)

        # Data.set_data_item(key="hpk_maps", value=response['maps'])

    def sync_hpk_players(self):
        pass

    def translate_scoville_maps(self, uuid_list):
        return [self.scoville_course_map[map] for map in uuid_list]

    def get_all_verified_users(self):
        data = Data.get_all_items(table="verified", name="verification")
        return [player['value']['uuid'] for player in data]

def setup(bot):
    # This is called by interactions.py so it knows how to load the Extension
    AutoSync(bot)