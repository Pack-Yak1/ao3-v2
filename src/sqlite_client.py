"""
Module for database connections
"""
import typing
import sqlite3 as sl
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

    def insert_tag(self, tag_name: str, tag_id: int) -> None:
        cursor = self.connection.cursor()
        query = """
            INSERT OR IGNORE INTO tags(tag_id, tag_name)
            VALUES (?, ?)
        """
        cursor.execute(query, [tag_id, tag_name])
        if cursor.rowcount != 0:
            print(f"Saved id {tag_id} for tag: {tag_name}")
        self.connection.commit()

    def get_tag_name(self, tag_id: int) -> str | None:
        resp = self.query("SELECT tag_name FROM tags WHERE tag_id = ?", [tag_id])
        if len(resp) == 0:
            return None
        return resp[0][0]

    def get_tag_id(self, tag_name: str) -> int | None:
        resp = self.query("SELECT tag_id FROM tags WHERE tag_name = ?", [tag_name])
        if len(resp) == 0:
            return None
        return resp[0][0]

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
        self.connection.commit()

    def query(self, query: str, *params: tuple) -> list:
        if self.connection is None:
            raise Exception("Database connection not initialized.`")

        cursor = self.connection.cursor()
        cursor.execute(query, *params)
        resp = cursor.fetchall()
        cursor.close()
        self.connection.commit()
        return resp
