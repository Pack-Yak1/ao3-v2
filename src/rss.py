"""This module is used to find the RSS feeds associated with tags on AO3 and scrape the links obtained"""
import typing
import time
import threading
import requests
from bs4 import BeautifulSoup
import xmltodict
from dateutil.parser import isoparse
from sqlite_client import SqlClient, WorkType


ROOT = "https://archiveofourown.org"


class NoRssException(Exception):
    """
    Exception class raised when user attempts to track a tag without RSS support
    from AO3.
    """

    def __init__(self, tag):
        self.tag = tag
        self.msg = f"No RSS feed was found for tag: '{tag}'. Try getting the tag id yourself and using that instead"
        super().__init__(self.msg)


class RssHandler:
    """Class for handling AO3 RSS feeds"""

    def __init__(self, insert_delay):
        if insert_delay <= 0:
            raise ValueError(
                "RssHandler must be called with a positive value for `insert_delay`"
            )
        self.insert_delay = insert_delay
        self.buffer: typing.List[WorkType] = []
        self.buffer_lock = threading.Lock()
        self.last_insert_time = time.time()
        threading.Thread(
            group=None,
            target=self.__main_insert_works,
            name="Inserter",
        ).start()

    @staticmethod
    def get_rss_link(tag_name: str) -> typing.Tuple[str, str, int]:
        """
        Returns a tuple of the AO3 RSS feed link associated with `tag_name`, the tag id,
        and the name of the tag officially on AO3.

        If `tag` does not correspond to a tag on AO3 with an RSS, throws a
        NoRssException
        """
        url = f"https://archiveofourown.org/tags/{tag_name.replace('.', '*d*')}/works"

        with requests.session() as session:
            response = session.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            rss_soup = soup.find("a", {"title": "RSS Feed"})
            if rss_soup is None:
                raise NoRssException(tag_name)
            rel_link: str = rss_soup["href"]
            link = f"{ROOT}{rel_link}"

            tag_name = soup.find("a", {"class": "tag"}).contents[0]
            tag_id = rel_link.split("/")[2]
            return link, tag_name, int(tag_id)

    @staticmethod
    def resolve_tag_id_or_name(
        value: typing.Union[str, int],
    ) -> typing.Tuple[typing.Union[str, None], int]:
        """
        Given either a tag id (int) or tag name (str), find the latter. Name
        returned could be `None` if it's not been seen before
        """
        with SqlClient() as client:
            if isinstance(value, str):
                tag_name = value
                # We have the name, try to get id from local db
                tag_id = client.get_tag_id(value)
                if tag_id is None:
                    # We haven't seen an exact match for this name, query ao3
                    _, tag_name, tag_id = RssHandler.get_rss_link(value)

                # Save this tag name for future use
                client.insert_tag(tag_name, tag_id)
            else:
                tag_id = value
                tag_name = client.get_tag_name(tag_id)

        return tag_name, tag_id

    def scrape_tag_name_or_id(self, tag_name_or_id: typing.Union[str, int]) -> None:
        child = threading.Thread(
            group=None,
            target=self.__scrape_tag,
            name=tag_name_or_id,
            args=(tag_name_or_id,),
        )
        child.start()

    def __scrape_tag(self, tag_name_or_id: typing.Union[str, int]):
        """
        Main function for a daemon process that periodically scrapes `url`.

        `tag_name` need not be the true tag name, it is purely for logging
        `url` is the url of the rss feed to scrape periodically\n
        """

        if isinstance(tag_name_or_id, str):
            url, tag_name, tag_id = RssHandler.get_rss_link(tag_name_or_id)
            with SqlClient() as client:
                client.insert_tag(tag_name, tag_id)

        else:
            tag_name, tag_id = RssHandler.resolve_tag_id_or_name(tag_name_or_id)
            url = f"https://archiveofourown.org/tags/{tag_id}/feed.atom"

        with requests.session() as session:
            while True:
                response = session.get(url)
                dic = xmltodict.parse(response.content)

                if tag_name is None:
                    # Save this title, tag_id pair for reference
                    with SqlClient() as client:
                        tag_name = dic["feed"]["title"].split("'")[-2]
                        client.insert_tag(tag_name, tag_id)

                entries = dic["feed"]["entry"]

                to_insert: typing.List[WorkType] = []
                for entry in entries:
                    title: str = entry["title"]
                    work_id: int = int(entry["id"].split("/")[-1])
                    published_time = isoparse(entry["published"]).timestamp()
                    to_insert.append((tag_id, work_id, title, published_time))

                print(f"""Got {len(entries)} works for \"{tag_name}\"""")

                self.__thread_insert_works(to_insert)

                time.sleep(self.insert_delay)

    def __main_insert_works(self):
        with SqlClient() as sqlite_client:
            while True:
                time.sleep(self.insert_delay)
                if len(self.buffer) > 0:
                    print(f"Attempting to insert {len(self.buffer)} works to database")
                    with self.buffer_lock:
                        sqlite_client.insert_works(self.buffer)
                        self.buffer = []

    def __thread_insert_works(
        self,
        works: typing.List[
            typing.Tuple[
                int,
                int,
                str,
                float,
            ]
        ],
    ):
        with self.buffer_lock:
            self.buffer += works
