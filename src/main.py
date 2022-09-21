"""
Entry point for the ingester. Load config variables and initialize daemons for ingestion
"""
from tkinter import messagebox
from rss import NoRssException, RssHandler
from frontend import AnalysisGui
from config import config


def main():
    rss = RssHandler(config["insert_delay"])
    for tag in config["favorite_tags"]:
        try:
            rss.scrape_tag_name_or_id(tag)
        except NoRssException as exc:
            messagebox.showwarning(exc.msg)
    for tag_id in config["favorite_tag_ids"]:
        try:
            rss.scrape_tag_name_or_id(tag_id)
        except NoRssException as exc:
            messagebox.showwarning(exc.msg)
    gui = AnalysisGui()
    gui.main()


if __name__ == "__main__":
    main()
