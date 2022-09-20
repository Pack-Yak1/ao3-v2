"""
Module for database connections
"""
import time
import typing
import sqlite3 as sl
import ciso8601
from config import config


WorkType = typing.Tuple[
    int,
    int,
    str,
    float,
]


class SqlClient:
    """
    Class used to interact with db
    """

    connection = None

    def __init__(self):
        connection = sl.connect(config["database_file_name"])
        print("Initializing database")
        with open("schema.sql", "r", encoding="utf-8") as schema_fd:
            schema = schema_fd.read().split(";")
        for create_table_command in schema:
            connection.execute(create_table_command)
        print("Database initialized")

        connection.commit()
        connection.close()

    def __enter__(self):
        self.connection = sl.connect(config["database_file_name"])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        if exc_type is not None:
            print("\nExecution type:", exc_type)
        if exc_value is not None:
            print("\nExecution value:", exc_value)
        if traceback is not None:
            print("\nTraceback:", traceback)

    def insert_works(
        self,
        works: typing.List[WorkType],
    ) -> None:
        if len(works) == 0:
            return
        cursor = self.connection.cursor()
        query = """
            INSERT OR IGNORE INTO works(tag_id, work_id, title, timestamp)
            VALUES (?, ?, ?, ?)
        """
        cursor.executemany(query, works)
        print(f"Inserted {cursor.rowcount} rows")
        print(works)
        self.connection.commit()

    def get_hourly_stats(self, tag_name_or_id: str|int, begin_time: float, end_time: float):
        resp = self.__query()

    def __query(self, query: str, **params: dict) -> list:
        if self.connection is None:
            raise Exception("Database connection not initialized.`")

        cursor = self.connection.cursor()
        cursor.execute(query, **params)
        resp = cursor.fetchall()
        cursor.close()
        return resp


def get_time(iso_string: str) -> float:
    timestamp = ciso8601.parse_datetime(iso_string)
    return time.mktime(timestamp.timetuple())
