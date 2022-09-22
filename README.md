# AO3 Tools for Windows

## Setting up:

Download the zip in the release and unzip it. Alternatively, download the source
code and create a Python virtual environment. Run `pip install -r requirements.txt`
to install the necessary dependencies. `cd` into `src` and run `build.bat`. The
`dist` folder produced will contain an `AO3 Tools` folder with all necessary files

## Configuring your scraper

Save the tags you'd like to track in `AO3 Tools/config/default.json`. The `favorite_tags`
field is an array of strings and the `favorite_tag_ids` field is an array of ints.
Tag ids can be found by clicking the RSS Feed on the top right of a tag page on AO3.
The number in the url to the right of `tags` is the tag id.

You can change the frequency with which works are checked by changing the
`insert_delay` field which represents the time between requests in seconds.

## Running the scraper

In the `AO3 Tools` folder, double click the `AO3 Tools` executable.

## Usage

Enter either a tag name or id and select the granularity, start and end times to
see a breakdown of post creation times when you click the `Get stats` button.
Searching by tag id or exact matches for tag names will be faster than doing a
fuzzy wordsearch. To see all tag names and ids encountered before, click the
`Tags saved` button
