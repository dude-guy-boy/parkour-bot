import inspect
from os import path
from tinydb import TinyDB, Query

class BaseDataBase:
    def _get_db_and_query(self, directory: str, table: str = "default", name: str = None):
        '''
        Gets the TinyDB database and query using the name of the module
        as reference.
        '''
        
        # Get the name of the extension accessing the database
        if not name:
            for thing in inspect.stack():
                file = inspect.getmodule(thing[0]).__file__
                if "extensions" in file:
                    name = path.basename(file)[:-3]
                    break

                if "src" and not "database" in file:
                    name = path.basename(file)[:-3]
                    break

        db = TinyDB(f"./{directory}/{name}.json").table(table)
        query = Query()

        return db, query
    
    def _init_item(self, key, value, directory: str, table: str = "default", name: str = None):
        '''Initialises the item if it does not yet exist'''

        db, query = self._get_db_and_query(self, directory, table, name)

        # If item doesnt exist, create it
        if not db.search(query.key == key):
            db.insert({"key": key, "value": value})

    def _get_item(self, key, directory: str, table: str = "default", name: str = None):
        '''Gets an item'''

        db, query = self._get_db_and_query(self, directory, table, name)

        # Return the item
        return db.search(query.key == key)
    
    def _set_item(self, key, value, directory: str, table: str = "default", name: str = None):
        '''Sets an item'''

        db, query = self._get_db_and_query(self, directory, table, name)

        self._init_item(self, key=key, value=value, table=table, directory=directory, name=name)

        db.update({"key": key, "value": value}, query.key == key)

class Config(BaseDataBase):
    @classmethod
    def get_config_parameter(cls, key: str) -> list:
        '''Gets a config parameter'''

        return cls._get_item(cls, key=key, directory="config")[0]['value']

    @classmethod
    def set_config_parameter(cls, key: str, value):
        '''Sets a config parameter'''

        cls._set_item(cls, key=key, value=value, directory="config")

class Data(BaseDataBase):
    @classmethod
    def get_data_item(cls, key: str, table: str = "default", name: str = None) -> list:
        '''Gets a data item'''

        return cls._get_item(cls, key=key, directory="data", table=table, name=name)[0]['value']

    @classmethod
    def set_data_item(cls, key: str, value, table: str = "default", name: str = None):
        '''Sets a data item'''

        cls._set_item(cls, key=key, value=value, directory="data", table=table, name=name)

    @classmethod
    def get_item_from_start(cls, key_start: str, table: str = "default", name: str = None) -> list:
        '''Gets a data item. Returns key, value'''

        db, query = cls._get_db_and_query(cls, directory="data", table=table, name=name)

        # Return the data item
        return db.search(query.key.test(lambda s: str(s).startswith(str(key_start))))[0]['key'], db.search(query.key.test(lambda s: str(s).startswith(str(key_start))))[0]['value']

    @classmethod
    def delete_item(cls, item: dict, table: str = "default", name: str = None):
        '''Deletes a data item'''

        db, query = cls._get_db_and_query(cls, directory="data", table=table, name=name)

        record = db.search(query.key == item['key'] and query.value == item['value'])

        db.remove(doc_ids=[record[0].doc_id])

    @classmethod
    def get_all_items(cls, table: str = "default", name: str = None) -> list:
        '''Gets all items in a table'''

        db, _ = cls._get_db_and_query(cls, directory="data", table=table, name=name)

        return db.all()
    
class UserData(Data):
    @classmethod
    def get_user(cls, id, table: str = "default"):
        '''Gets a user'''
        try:
            return cls.get_data_item(key=str(id), table=table)
        except:
            cls._init_item(cls, key=str(id), value=[], directory="data", table=table)
            return cls.get_data_item(key=str(id), table=table)

    @classmethod
    def set_user(cls, id, data, table: str = "default"):
        '''Sets a users data'''
        cls.set_data_item(key=str(id), value=data, table=table)

    @classmethod
    def delete_user(cls, id, table):
        '''Deletes a user'''
        user = cls.get_user(id, table=table)

        cls.delete_item(item=user, table=table)