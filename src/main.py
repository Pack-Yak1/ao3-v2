"""
Entry point for the ingester. Load config variables and initialize daemons for ingestion
"""
from rss import RssHandler
from config import config


def main():
    rss = RssHandler(config["insert_delay"])
    for tag in config["favorite_tags"]:
        rss.scrape_tag(tag)
    for tag_id in config["favorite_tag_ids"]:
        rss.scrape_tag_id(tag_id)


if __name__ == "__main__":
    main()
