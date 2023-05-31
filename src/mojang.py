import requests

class MojangAPI:
    @classmethod
    def get_uuid_from_name(self, name: str):
        req = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}")

        try:
            req.json()
        except:
            return None

        return req.json()['id']