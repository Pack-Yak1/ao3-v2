"""Module for interfacing with user"""
from sqlite_client import SqlClient
from rss import RssHandler
from config import config


formats = {"hour": "%H", "day of week": "%w", "month": "%-m", "year": "%Y"}


class UserClient:
    """Class for handling and displaying user requests for data"""

    def __init__(self):
        self.rss_handler = RssHandler(config["insert_delay"])

    def get_stats(
        self,
        tag_name_or_id: str | int,
        granularity: str,
        begin_time: float,
        end_time: float,
    ):
        if granularity not in formats:
            raise ValueError(
                f"Unsupported granularity: '{granularity}'. Must be one of {', '.join(list(formats.keys()))}"
            )

        if isinstance(tag_name_or_id, str):
            tag_id = RssHandler.get_rss_link(tag_name_or_id)[2]
        else:
            tag_id = tag_name_or_id

        with SqlClient() as client:
            resp = client.query(
                """
                SELECT
                    COUNT(*),
                    strftime(?, datetime(timestamp, 'unixepoch')) AS granularity
                FROM works
                WHERE
                    tag_id = ? AND
                    timestamp BETWEEN ? AND ?
                GROUP BY granularity
            """,
                (formats.get(granularity), tag_id, begin_time, end_time),
            )
            print(resp)


c = UserClient()
c.get_stats("Spy x Family (Manga)", "day of week", 0, 10000000000)
