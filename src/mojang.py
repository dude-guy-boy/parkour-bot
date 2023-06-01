import requests

class MojangAPI:
    @classmethod
    def get_uuid_from_name(cls, name: str):
        req = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}")

        try:
            req.json()
        except:
            return None

        return req.json()['id']
    
    @classmethod
    def get_name_from_uuid(cls, uuid: str):
        req = requests.get(f"https://api.mojang.com/user/profile/{uuid}")
        try:
            req.json()
        except:
            return None

        return req.json()['name']