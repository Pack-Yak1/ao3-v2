"""Module for interfacing with user"""
from datetime import datetime
import typing
from tkinter import (
    OptionMenu,
    Text,
    Tk,
    Button,
    Entry,
    StringVar,
    Label,
    Toplevel,
    messagebox,
)
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from tkcalendar import Calendar
from sqlite_client import SqlClient, FORMATS
from rss import RssHandler, NoRssException
from config import config

fprop = fm.FontProperties(fname="NotoSerifJP-Regular.otf")


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

        def get_stats_button_function() -> None:
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
        get_stats_button = Button(
            self.root, width=10, text="Get stats", command=get_stats_button_function
        )
        get_stats_button.grid(column=2, row=1, padx=10, pady=10)

        def show_tags_function():
            with SqlClient() as client:
                data = client.get_all_tags()
                text_data = "\n".join(
                    list(map(lambda tup: f"""{tup[0]:<15}| {tup[1]}""", data))
                )

            window = Toplevel(self.root)
            window.state("zoomed")
            window.title("Tags with saved data")
            textbox = Text(window, height=100, width=100)
            textbox.insert("1.0", text_data)
            textbox.pack(fill="both")

        # Show tags button
        show_tags_button = Button(
            self.root, width=10, text="Tags saved", command=show_tags_function
        )
        show_tags_button.grid(column=2, row=2, padx=10, pady=10)


class UserClient:
    """Class for handling and displaying user requests for data"""

    def __init__(self):
        self.rss_handler = RssHandler(config["insert_delay"])

    def show_distribution(
        self,
        tag_name_or_id: typing.Union[str, int],
        granularity: str,
        begin_time: float,
        end_time: float,
    ) -> None:
        tag_name, tag_id = RssHandler.resolve_tag_id_or_name(tag_name_or_id)

        with SqlClient() as client:
            data = client.get_works_by_granularity(
                tag_id, granularity, begin_time, end_time
            )

        default_tups = FORMATS.get(granularity)["default"]
        labels = []
        heights = []

        if default_tups is not None:
            default = list(map(lambda x: x[1], default_tups))
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
        axis.set_xlabel(granularity.title(), fontsize=14)
        axis.set_ylabel("Relative Frequency (%)", fontsize=14)
        axis.set_xticks(x_vals)
        axis.set_xticklabels(labels)
        axis.set_ybound(0, None)
        axis.set_title(
            f"Breakdown of posts for {tag_name} (tag id: {tag_id}) by {granularity}",
            fontproperties=fprop,
            fontsize=18,
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
