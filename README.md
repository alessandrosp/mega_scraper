# MegaScraper

Command-line tool to recursively download images from a given website.

The command below would download any single picture on the site https://mugshots.com/.

`python mega_scraper.py -s https://mugshots.com/`

MegaScraper implements a series of flags that can be used to customize its behaviour. For example, the following command would download 100 images with a minimum width and height of 300px from https://mugshots.com/.

`python mega_scraper.py -s https://mugshots.com/ -hm 100 -mw 300 -mh 300`

A full list of flags can be found below.

## Install

In order to use MegaScraper you'll need to install all its dependencies. The easiest way to do so is to follow these steps:

1. Download the package from https://github.com/.
1. Use virtualenv to create virtual enviroment: `virtualenv -p python3 venv`.
1. Activate the virtual enviroment: `source venv/bin/activate`
1. Install the requirements: `pip install -r requirements.txt`.

That's it.

While MegaScraper was developed to be used as a command-line tool, nothing prevents you from importing it as if it was a regular Python package. For example:

```python
import mega_scraper

url = 'https://mugshots.com/'
scraper = mega_scraper.MegaScraper(url)
scraper.scrape(max_pages=10)
scraper.download(how_many=100)
```

Note however that MegaScraper is not currently on PyPI so you won't be able to install via `pip`. Just download `mega_scraper.py` from GitHub.

## Flags

Below you can find a list of all flags currently supported by MegaScraper. You can find additional and more granular documentation in the `mega_scraper.py` file itselt.

- `--seed` or `-s` to specify the seed URL. It's the only non-optional flag.
- `--regex_pages` or `-rp` to specify from which pages to download images.
- `--regex_images` or `-ri` to specify which images URLs to consider.
- `--min_width` or `-mw` to specify the minimum width an image has to have to be downloaded.
- `--min_height` or `-mh` to specify the minimum height an image has to have to be downloaded.
- `--output_folderpath` or `-of` to specify the folder where to output.
- `--output_structure` or `-os` to specify the output structure (either `flat` or `grouped`).
- `--output_naming` or `-on` to specify the naming system for the output files (either `keep` or `numerical`).
- `--images_per_folder` or `-if` to specify how many images per folder when `grouped`.
- `--folder_initial_num` or `-fn` to specify the number for the first folder when `grouped`.
- `--max_pages` or `-mp` to specify the maximum number of pages to crawl.
- `--how_many` or `-hm` to specify how many images to download.
