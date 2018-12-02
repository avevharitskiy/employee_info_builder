import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import DictCursor
from helpers import Configuration


class Database():

    @classmethod
    def __init_database(cls, connection_dict: dict):
        """
        Create database.

        :param connection_dict: connection params
        :type connection_dict: dict
        """
        # connect to defult PostreSQL database
        conn = psycopg2.connect(
            dbname='postgres',
            user=connection_dict['user'],
            password=connection_dict['password'],
            host=connection_dict['host'])

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()
        # crete database
        cursor.execute('CREATE DATABASE "%s" ;' % connection_dict['dbname'])
        conn.close()
        # connect to created database
        conn = psycopg2.connect(**connection_dict)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        queries = (
            # UserActivity table creation
            """
                CREATE TABLE "UserActivity" (
                    "UserID" integer NOT NULL,
                    "Date" date,
                    "Category" text,
                    "Useful" smallint,
                    "WastedTime" interval
                )
                WITH (
                    OIDS=FALSE
                );
            """,
            # UserLocation table creation
            """
                CREATE TABLE "UserLocation"(
                    "UserID" integer NOT NULL,
                    "DateTime" timestamp with time zone,
                    "Status" smallint
                )
                WITH (
                    OIDS=FALSE
                );
            """,
            # UserOverwork table creation
            """
                CREATE TABLE "UserOverwork"(
                    "UserID" integer NOT NULL,
                    "Overwork" interval,
                    "Date" date
                )
                WITH (
                    OIDS=FALSE
                );
            """,
            # UserPlanPercent table creation
            """
                CREATE TABLE "UserPlanPercent"(
                    "UserID" integer NOT NULL,
                    "PlanPercent" smallint
                )
                WITH (
                    OIDS=FALSE
                );
            """,
            # MinedUsers table creation
            """
                CREATE TABLE "MinedUsers"(
                    "UserID" integer NOT NULL,
                    "TotalDays" integer
                )
                WITH (
                    OIDS=FALSE
                );
            """
            # User neural_data table
            """
                CREATE TABLE "UsersNeuralData"(
                    "UserID" integer NOT NULL,
                    "UserFirstCalls" real,
                    "UserLastCalls" real,
                    "UserFirstDuration" real,
                    "UserLastDuration" real,
                    "UserFirstOverwork" real,
                    "UserLastOverwork" real
                )
                WITH (
                    OIDS=FALSE
                );
            """


        )
        # create tables
        for query in queries:
            cursor.execute(query)

        conn.close()

        cls.connect_to_database(connection_dict)

    @classmethod
    def connect_to_database(cls, connection_dict: dict = None):
        """
        Connect to database. If databse not found create it.

        :param connection_dict: connection params, defaults to None
        :param connection_dict: dict, optional
        """

        # if connection params is empty, read they from core config
        if not connection_dict:
            config = Configuration.app_config
            db_connection_fields = set(['host', 'dbname', 'user', 'password'])

            if not config['Database'] or (db_connection_fields - set(config['Database'])):
                raise KeyError('В файле конфигурации отсутвуют данные о подключении к БД')

            connection_dict = {key: value for key, value in config['Database'].items() if key in db_connection_fields}

        # try connect to database
        try:
            cls.__connection = psycopg2.connect(**connection_dict)
            cls.__cursor = cls.__connection.cursor(cursor_factory=DictCursor)
        except psycopg2.OperationalError:
            # if database not found create database
            cls.__init_database(connection_dict)

    @classmethod
    def query(cls, query_str: str, fields=None):
        cls.__cursor.execute(query_str, fields)

        if cls.__cursor.description:
            return cls.__cursor.fetchall()

    @classmethod
    def query_row(cls, query_str: str, fields=None):
        cls.__cursor.execute(query_str, fields)

        if cls.__cursor.description:
            data = cls.__cursor.fetchall()
            return data[0] if data else None

    @classmethod
    def commit_changes(cls):
        cls.__connection.commit()
