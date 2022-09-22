"""
Entry point for the ingester. Load config variables and initialize daemons for ingestion
"""
import traceback
from rss import RssHandler
from frontend import AnalysisGui
from config import config


def main():
    try:
        with RssHandler(config["insert_delay"]) as rss:
            for tag in config["favorite_tags"]:
                rss.scrape_tag_name_or_id(tag)
            for tag_id in config["favorite_tag_ids"]:
                rss.scrape_tag_name_or_id(tag_id)

            gui = AnalysisGui()
            gui.main()

    except Exception:
        with open("logs.txt", "w", encoding="utf-8") as log:
            tb = traceback.format_exc()
            log.write(tb)


if __name__ == "__main__":
    main()
