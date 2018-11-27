from helpers import Configuration

import psycopg2


class Database():

    @classmethod
    def connect_to_database(cls):
        config = Configuration.app_config
        db_connection_fields = set(['host', 'dbname', 'user', 'password'])

        if not config['Database'] or (db_connection_fields - set(config['Database'])):
            raise KeyError('В файле конфигурации отсутвуют данные о подключении к БД')

        connection_dict = {key: value for key, value in config['Database'].items() if key in db_connection_fields}

        cls.__connection = psycopg2.connect(**connection_dict)

        cls.__cursor = cls.__connection.cursor()

    @classmethod
    def query(cls, query_str: str):
        cls.__cursor.execute(query_str)
        cls.__connection.commit()

        return cls.__cursor.fetchall()
