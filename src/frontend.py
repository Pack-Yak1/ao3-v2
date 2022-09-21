"""Module for interfacing with user"""
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from tkinter import OptionMenu, Tk, Button, Entry, StringVar, Label, messagebox
from tkcalendar import Calendar
from sqlite_client import SqlClient
from rss import RssHandler, NoRssException
from config import config
from typing import List, Tuple


FORMATS = {
    "hour": {"fmt": "%H", "default": [str(i) for i in range(24)]},
    "day of week": {"fmt": "%w", "default": [str(i) for i in range(7)]},
    "month": {"fmt": "%m", "default": [f"{i:02}" for i in range(12)]},
    "year": {"fmt": "%Y", "default": None},
}

VALID_GRANULARITIES_STRING = ", ".join(list(map(lambda s: f"'{s}'", FORMATS.keys())))


class AnalysisGui:
    def __init__(self):
        self.user_client = UserClient()
        self.root = Tk()

    def main(self):
        self.root.title("Pack Yak1's AO3 Scraper")
        self.root.configure(background="grey")

        # Tag name
        tag_label = Label(self.root, text="Tag name", width=15)
        tag_label.grid(column=0, row=0, padx=10, pady=10)
        tag_string = StringVar(value="Enter a tag name")
        tag_input = Entry(self.root, width=65, textvariable=tag_string)
        tag_input.grid(column=1, row=0, padx=10, pady=10)

        # Tag id
        tag_id_label = Label(self.root, text="Tag id", width=15)
        tag_id_label.grid(column=0, row=1, padx=10, pady=10)
        tag_id_string = StringVar(
            value="Enter a tag id (takes precedence over name if you enter a number)"
        )
        tag_id_input = Entry(self.root, width=65, textvariable=tag_id_string)
        tag_id_input.grid(column=1, row=1, padx=10, pady=10)

        # Granularity
        granularity_label = Label(self.root, text="Granularity", width=15)
        granularity_label.grid(column=0, row=2, padx=10, pady=10)
        granularity_selection = StringVar(value=list(FORMATS.keys())[0].title())
        granularity_input = OptionMenu(
            self.root,
            granularity_selection,
            *list(map(lambda s: s.title(), FORMATS.keys())),
        )
        granularity_input.grid(column=1, row=2, padx=10, pady=10, sticky="NSEW")

        now = datetime.now()

        # Begin time
        begin_time_label = Label(self.root, text="Begin time", width=15)
        begin_time_label.grid(column=0, row=3, padx=10, pady=10, sticky="N")
        begin_time_input = Calendar(
            self.root, selectmode="day", year=now.year, month=now.month, day=now.day - 1
        )
        begin_time_input.grid(column=1, row=3, padx=10, pady=10, sticky="EW")

        # End time
        end_time_label = Label(self.root, text="End time", width=15)
        end_time_label.grid(column=0, row=4, padx=10, pady=10, sticky="N")
        end_time_input = Calendar(
            self.root, selectmode="day", year=now.year, month=now.month, day=now.day
        )
        end_time_input.grid(column=1, row=4, padx=10, pady=10, sticky="EW")

        def button_function() -> None:
            try:
                tag = (
                    int(tag_id_string.get())
                    if tag_id_string.get().isdigit()
                    else tag_string.get()
                )
                granularity = granularity_selection.get().lower()
                begin_time = datetime.strptime(
                    begin_time_input.get_date(), "%m/%d/%y"
                ).timestamp()
                end_time = datetime.strptime(
                    end_time_input.get_date(), "%m/%d/%y"
                ).timestamp()
                self.user_client.show_distribution(
                    tag, granularity, begin_time, end_time
                )
            except NoRssException:
                messagebox.showinfo(
                    "No such tag found",
                    f"No tag could be found when searching for '{tag}'",
                )

        # Get stats button
        button = Button(self.root, width=10, text="Get stats", command=button_function)
        button.grid(column=2, row=1, padx=10, pady=10)


class UserClient:
    """Class for handling and displaying user requests for data"""

    def __init__(self):
        self.rss_handler = RssHandler(config["insert_delay"])

    def get_stats(
        self,
        tag_id: int,
        granularity: str,
        begin_time: float,
        end_time: float,
    ) -> List[Tuple[str, int]]:
        if granularity not in FORMATS:
            raise ValueError(
                f"Unsupported granularity: '{granularity}'. "
                f"Must be one of: {VALID_GRANULARITIES_STRING}"
            )

        with SqlClient() as client:
            resp = client.query(
                """
                SELECT
                    strftime(?, datetime(timestamp, 'unixepoch')) AS granularity,
                    COUNT(*)
                FROM works
                WHERE
                    tag_id = ? AND
                    timestamp BETWEEN ? AND ?
                GROUP BY granularity
                ORDER BY granularity
            """,
                (FORMATS.get(granularity)["fmt"], tag_id, begin_time, end_time),
            )
            return resp

    def show_distribution(
        self,
        tag_name_or_id: str | int,
        granularity: str,
        begin_time: float,
        end_time: float,
    ) -> None:
        tag_name, tag_id = RssHandler.resolve_tag_id_or_name(tag_name_or_id)

        data = self.get_stats(tag_id, granularity, begin_time, end_time)

        default = FORMATS.get(granularity)["default"]
        labels = []
        heights = []

        if default is not None:
            for label in default:
                labels.append(label)
                height = 0
                # Pretty much constant time, not going to overoptimize
                for _label, _height in data:
                    if _label == label:
                        height = _height
                heights.append(height)

        else:
            for group, y_val in data:
                labels.append(group)
                heights.append(y_val)

        x_vals = np.arange(len(labels))
        normalizer = np.sum(heights)
        y_vals = np.array(heights) / (normalizer if normalizer != 0 else 1) * 100
        _, axis = plt.subplots()

        axis.bar(
            x_vals,
            y_vals,
            width=1,
            edgecolor="black",
            linewidth=2,
        )
        axis.set_xlabel(granularity.title())
        axis.set_ylabel("Relative Frequency (%)")
        axis.set_xticks(x_vals)
        axis.set_xticklabels(labels)
        axis.set_ybound(0, None)
        axis.set_title(
            f"Breakdown of posts for {tag_name} (tag id: {tag_id}) by {granularity}"
        )

        for (x_val, y_val), raw_val in zip(
            np.hstack((x_vals.reshape(-1, 1), y_vals.reshape(-1, 1))), heights
        ):
            axis.text(
                x_val,
                y_val + 0.4,
                f"{raw_val} post{'s' if raw_val != 1 else ''}",
                horizontalalignment="center",
            )

        mng = plt.get_current_fig_manager()
        mng.window.state("zoomed")
        plt.show()
