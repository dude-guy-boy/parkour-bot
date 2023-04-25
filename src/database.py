import inspect
from os import path
from tinydb import TinyDB, Query

class Config:
    def __get_db_and_query(self):
        '''
        Gets the TinyDB database and query using the name of the module
        as reference.
        '''
        
        # Get the name of the extension modifying config
        name = path.basename(inspect.getmodule(inspect.stack()[2][0]).__file__)[:-3]

        if(name == "database"):
            name = path.basename(inspect.getmodule(inspect.stack()[3][0]).__file__)[:-3]

        db = TinyDB(f"./config/{name}.json").table("config")
        query = Query()

        return db, query

    @classmethod
    def init_config_parameter(cls, parameter: dict):
        '''Initialises the config parameter if it does not yet exist'''

        db, query = cls.__get_db_and_query(cls)

        # If parameter is not in config, insert it
        if not db.search(query.key == str(list(parameter)[0])):
            db.insert({"key": str(list(parameter)[0]), "value": parameter[list(parameter)[0]]})

    @classmethod
    def get_config_parameter(cls, key: str) -> list:
        '''Gets a config parameter'''

        db, query = cls.__get_db_and_query(cls)

        # Return the config item
        return db.search(query.key == str(key))[0]['value']

    @classmethod
    def set_config_parameter(cls, parameter: dict):
        '''Sets a config parameter'''

        db, query = cls.__get_db_and_query(cls)

        cls.init_config_parameter(parameter)

        db.update({"key": str(list(parameter)[0]), "value": parameter[list(parameter)[0]]}, query.key == str(list(parameter)[0]))

class Data:
    def __get_db_and_query(self, table: str):
        '''
        Gets the TinyDB database and query using the name of the module
        as reference.
        '''
        
        # Get the name of the extension modifying config
        name = path.basename(inspect.getmodule(inspect.stack()[2][0]).__file__)[:-3]

        if(name == "database"):
            name = path.basename(inspect.getmodule(inspect.stack()[3][0]).__file__)[:-3]

        db = TinyDB(f"./data/{name}.json").table(table)
        query = Query()

        return db, query

    @classmethod
    def init_item(cls, table: str, item: dict):
        '''Initialises the data item if it does not yet exist'''

        db, query = cls.__get_db_and_query(cls, table)

        # If item is not in data, insert it
        if not db.search(query.key == str(list(item)[0])):
            db.insert({"key": str(list(item)[0]), "value": item[list(item)[0]]})

    @classmethod
    def get_item(cls, table: str, key: str) -> list:
        '''Gets a data item'''

        db, query = cls.__get_db_and_query(cls, table)

        # Return the data item
        return db.search(query.key == str(key))[0]['value']

    @classmethod
    def get_item_from_start(cls, table: str, key_start: str) -> list:
        '''Gets a data item. Returns key, value'''

        db, query = cls.__get_db_and_query(cls, table)

        # Return the data item
        return db.search(query.key.test(lambda s: str(s).startswith(str(key_start))))[0]['key'], db.search(query.key.test(lambda s: str(s).startswith(str(key_start))))[0]['value']

    @classmethod
    def set_item(cls, table: str, item: dict):
        '''Sets a data item'''

        db, query = cls.__get_db_and_query(cls, table)

        cls.init_item(table, item)

        db.update({"key": str(list(item)[0]), "value": item[list(item)[0]]}, query.key == str(list(item)[0]))

    @classmethod
    def delete_item(cls, table: str, item: dict):
        '''Deletes a data item'''

        db, query = cls.__get_db_and_query(cls, table)

        record = db.search(query.key == item['key'] and query.value == item['value'])

        db.remove(doc_ids=[record[0].doc_id])

    @classmethod
    def get_all_items(cls, table: str) -> list:
        '''Gets all items in a table'''

        db, query = cls.__get_db_and_query(cls, table)

        return db.all()