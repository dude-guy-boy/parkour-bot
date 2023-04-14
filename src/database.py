import inspect
from os import path
from tinydb import TinyDB, Query

class Config:
    def __get_db_and_query(self):
        '''
        Gets the TinyDB database and query using the name of the module
        as reference.
        '''
        
        name = path.basename(inspect.getmodule(inspect.stack()[2][0]).__file__)[:-3]

        db = TinyDB(f"./config/{name}.json").table("config")
        query = Query()

        return db, query

    @classmethod
    def init_config_parameter(cls, parameter: dict):
        '''Initialises the config parameter if it does not yet exist'''

        db, query = cls.__get_db_and_query(cls)

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

# TODO: class Data: