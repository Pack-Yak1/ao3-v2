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

FORMATS = {
    "hour": {
        "fmt": "%H",
        "ugly_fmt": "%H",
        "pretty_fmt": "%H",
        "default": [(str(i), str(i)) for i in range(24)],
    },
    "day of week": {
        "fmt": "%w",
        "ugly_fmt": "%w",
        "pretty_fmt": "%a",
        "default": [
            ("0", "Sun"),
            ("1", "Mon"),
            ("2", "Tue"),
            ("3", "Wed"),
            ("4", "Thu"),
            ("5", "Fri"),
            ("6", "Sat"),
        ],
    },
    "month": {
        "fmt": "%m",
        "ugly_fmt": "%m",
        "pretty_fmt": "%b",
        "default": [
            ("01", "Jan"),
            ("02", "Feb"),
            ("03", "Mar"),
            ("04", "Apr"),
            ("05", "May"),
            ("06", "Jun"),
            ("07", "Jul"),
            ("08", "Aug"),
            ("09", "Sep"),
            ("10", "Oct"),
            ("11", "Nov"),
            ("12", "Dec"),
        ],
    },
    "year": {"fmt": "%Y", "ugly_fmt": "%Y", "pretty_fmt": "%Y", "default": None},
}

VALID_GRANULARITIES_STRING = ", ".join(list(map(lambda s: f"'{s}'", FORMATS.keys())))


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

    def __exit__(self, _exc_type, _exc_value, _traceback):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

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

    def get_tag_name(self, tag_id: int) -> typing.Union[str, None]:
        resp = self.query("SELECT tag_name FROM tags WHERE tag_id = ?", [tag_id])
        if len(resp) == 0:
            return None
        return resp[0][0]

    def get_tag_id(self, tag_name: str) -> typing.Union[int, None]:
        resp = self.query("SELECT tag_id FROM tags WHERE tag_name = ?", [tag_name])
        if len(resp) == 0:
            return None
        return resp[0][0]

    def get_all_tags(self) -> typing.List[typing.Tuple[int, str]]:
        resp = self.query("SELECT tag_id, tag_name FROM tags ORDER BY tag_name")
        return resp

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

    def get_works_by_granularity(
        self,
        tag_id: int,
        granularity: str,
        begin_time: float,
        end_time: float,
    ) -> typing.List[typing.Tuple[str, int]]:
        if granularity not in FORMATS:
            raise ValueError(
                f"Unsupported granularity: '{granularity}'. "
                f"Must be one of: {VALID_GRANULARITIES_STRING}"
            )
        query = """
            SELECT
                strftime(?, datetime(timestamp, 'unixepoch', 'localtime')) AS granularity,
                COUNT(*)
            FROM works
            WHERE
                tag_id = ? AND
                timestamp BETWEEN ? AND ?
            GROUP BY granularity
            ORDER BY granularity
        """
        db_format = FORMATS.get(granularity)["fmt"]
        resp = self.query(query, (db_format, tag_id, begin_time, end_time))
        print(resp)

        def prettify_label(tpl):
            old_label = tpl[0]
            default = FORMATS.get(granularity)["default"]
            new_label = old_label
            if default is not None:
                for old, new in default:
                    if old == old_label:
                        new_label = new
            return new_label, tpl[1]

        resp = list(map(prettify_label, resp))
        print(resp)
        return resp

    def query(self, query: str, *params: tuple) -> list:
        if self.connection is None:
            raise Exception("Database connection not initialized.`")

        cursor = self.connection.cursor()
        cursor.execute(query, *params)
        resp = cursor.fetchall()
        cursor.close()
        self.connection.commit()
        return resp
