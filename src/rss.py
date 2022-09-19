"""This module is used to find the RSS feeds associated with tags on AO3 and scrape the links obtained"""
import typing
import time
import threading
import requests
from bs4 import BeautifulSoup
import xmltodict
from sqlite_client import SqlClient, get_time, WorkType

ROOT = "https://archiveofourown.org"


class NoRssException(Exception):
    """
    Exception class raised when user attempts to track a tag without RSS support
    from AO3.
    """

    def __init__(self, tag):
        super().__init__(f"No RSS feed was found for tag: '{tag}'")


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

    def __main_insert_works(self):
        with SqlClient() as sqlite_client:
            while True:
                time.sleep(self.insert_delay)
                if len(self.buffer) > 0:
                    print(f"Attempting to insert {len(self.buffer)} works to database")
                    with self.buffer_lock:
                        sqlite_client.insert_works(self.buffer)
                        self.buffer = []

    @staticmethod
    def get_rss_link(tag) -> typing.Tuple[str, str, int]:
        """
        Returns a tuple of the AO3 RSS feed link associated with `tag`, the tag id,
        and the name of the tag officially on AO3.

        If `tag` does not correspond to a tag on AO3 with an RSS, throws a
        NoRssException
        """
        url = f"https://archiveofourown.org/tags/{tag}/works"

        with requests.session() as session:
            response = session.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            rss_soup = soup.find("a", {"title": "RSS Feed"})
            if rss_soup is None:
                raise NoRssException(tag)
            rel_link: str = rss_soup["href"]
            link = f"{ROOT}{rel_link}"

            tag_name = soup.find("a", {"class": "tag"}).contents[0]
            tag_id = rel_link.split("/")[2]
            return link, tag_name, int(tag_id)

    def scrape_tag_id(self, tag_id: int):
        tag_name = f"tag_id {tag_id}"
        child = threading.Thread(
            group=None,
            target=self.__scrape_tag_id,
            name=tag_name,
            args=(
                tag_id,
                tag_name,
                f"https://archiveofourown.org/tags/{tag_id}/feed.atom",
            ),
        )
        child.start()

    def scrape_tag(self, tag: str):
        link, tag_name, tag_id = RssHandler.get_rss_link(tag)
        print(f"Searching for tag {tag} returned {tag_name}")
        child = threading.Thread(
            group=None,
            target=self.__scrape_tag_id,
            name=tag_name,
            args=(tag_id, tag_name, link),
        )
        child.start()

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

    def __scrape_tag_id(self, tag_id: int, tag_name: str, url: str):
        """
        Main function for a daemon process that periodically scrapes `url`.

        `url` is the url of the rss feed to scrape periodically\n
        """

        with requests.session() as session:
            while True:
                response = session.get(url)
                dic = xmltodict.parse(response.content)
                entries = dic["feed"]["entry"]

                to_insert = []
                for entry in entries:
                    title: str = entry["title"]
                    work_id: int = int(entry["id"].split("/")[-1])
                    published_time = get_time(entry["published"])
                    to_insert.append((tag_id, work_id, title, published_time))

                print(f"""Got {len(entries)} works for \"{tag_name}\"""")

                self.__thread_insert_works(to_insert)

                time.sleep(self.insert_delay)
