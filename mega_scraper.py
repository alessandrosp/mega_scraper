"""MegaScraper: command-line tool to download images from a single website.

MegaScraper allows to recursively download all images from a given
website starting from a single URL (i.e., the seed). The user can
provide regexes for both the pages to download images from and
for the images URLs, so that only the relevant resources are actually
downloaded.

Additionally, the user can provide min width and height for the
images, and decide on how the output folder should be organized.

Examples:

    >>> python mega_scraper.py -s https://mugshots.com/ -mp 2 -hm 10

"""

import argparse
import os
import re
import urllib.parse

import bs4
import PIL.Image
import requests

_DEFAULT_REGEX_PAGES = r''
_DEFAULT_REGEX_IMAGES = r''
_DEFAULT_MIN_WIDTH = 0
_DEFAULT_MIN_HEIGHT = 0
_DEFAULT_OUTPUT_FOLDERPATH = 'scraped'
_DEFAULT_OUTPUT_STRUCTURE = 'flat'
_DEFAULT_OUTPUT_NAMING = 'keep'
_DEFAULT_IMAGES_PER_FOLDER = 100
_DEFAULT_FOLDER_INITIAL_NUM = 1
_DEFAULT_MAX_PAGES = 99999
_DEFAULT_HOW_MANY = 99999  # Number of images to download per call to download().
_OUTPUT_STRUCTURE_VALUES = ('flat', 'grouped')
_OUTPUT_NAMING_VALUES = ('keep', 'numerical')


class MegaScraper(object):
    """Scraper that downloads images from a website iteratively."""

    def __init__(
            self,
            seed: str,
            regex_pages: str = _DEFAULT_REGEX_PAGES,
            regex_images: str = _DEFAULT_REGEX_IMAGES,
            min_width: int = _DEFAULT_MIN_WIDTH,
            min_height: int = _DEFAULT_MIN_HEIGHT,
            output_folderpath: str = _DEFAULT_OUTPUT_FOLDERPATH,
            output_structure: str = _DEFAULT_OUTPUT_STRUCTURE,
            output_naming: str = _DEFAULT_OUTPUT_NAMING,
            images_per_folder: int = _DEFAULT_IMAGES_PER_FOLDER,
            folder_initial_num: int = _DEFAULT_FOLDER_INITIAL_NUM):
        """Constructor for MegaScraper.

        Args:
            seed: the URL to start the navigation from. For MegaScraper
                to work effectively, all URLs on the site must be
                reachable statrinf from the seed.
            regex_pages: only pages that match this regex will be
                downloaded resources from. Note that pages that don't
                match this regex will still be scraped for URLs.
            regex_images: only images URLs that match this regex
                will be considered.
            min_width: minimum width for an image to be downloaded.
            max_height: minimum height for an image to be downloaded.
            output_folderpath: the folder where to download the images.
            output_structure: one between ('flat', 'grouped'). If 'flat',
                then all the images are downloaded in the same folder. If
                'grouped', then the images are grouped into sub-folders.
            output_naming: one between ('keep', 'numerical'). If 'keep',
                then the original name of the file is used. If 'numerical',
                then images are renamed '1.jpg', '2.jpg', etc.
            images_per_folder: if output_structure is 'grouped', then this
                parameter dictates how many images should be grouped
                in a single folder.
            folder_initial_num: if output_structure is 'grouped', then
                this paramter dictates the number-name of the first folder.
                The numbers are always padded to have length 4.
        """
        assert output_structure in _OUTPUT_STRUCTURE_VALUES
        assert output_naming in _OUTPUT_NAMING_VALUES
        assert images_per_folder > 0
        assert folder_initial_num > 0
        self._seed = seed
        self._parsed_seed = urllib.parse.urlparse(seed)
        self._root = '{u.scheme}://{u.netloc}'.format(u=self._parsed_seed)
        print('--The root of the seed appears to be: {}'.format(self._root))
        self._regex_pages = regex_pages
        self._regex_images = regex_images
        self._min_width = min_width
        self._min_height = min_height
        self._output_folderpath = output_folderpath
        self._output_structure = output_structure
        self._output_naming = output_naming
        self._images_per_folder = images_per_folder
        self._folder_initial_num = folder_initial_num
        self._explored = set()
        self._unexplored = set([seed])
        self._images_urls = set()
        self._downloaded = set()
        self._downloaded_idx = 1

    def _extract_unexplored_pages(self, soup: bs4.BeautifulSoup) -> set:
        """Extracts all unxplored pages (URLs) from a soup.

        Args:
            soup: the BeautifulSoup() to extract pages from.

        Returns:
            A set of strings, each being the URL of an unexplored page.
        """
        unexplored_pages = set()
        elements = soup.find_all('a')
        for element in elements:
            href = element.get('href')
            if href:
                if href.startswith('/'):
                    href = self._root + href
                href_netloc = urllib.parse.urlparse(href).netloc
                if (href not in self._explored
                        and href_netloc == self._parsed_seed.netloc):
                    unexplored_pages.add(href)
        return unexplored_pages

    def _extract_images_urls(self, soup: bs4.BeautifulSoup) -> set:
        """Extracts all images URLs from a soup.

        Args:
            soup: the BeautifulSoup() to extract images URLs from.

        Returns:
            A set of strings, each being the URL of an image.
        """
        images_urls = set()
        elements = soup.find_all('img')
        for element in elements:
            src = element.get('src')
            if src and not src.endswith('.gif'):
                if src.startswith('/'):
                    src = self._root + src
                if re.search(self._regex_images, src):
                    images_urls.add(src)
        return images_urls

    def scrape(self, max_pages: int = _DEFAULT_MAX_PAGES) -> set:
        """Scrapes all images URLs from unexplored pages.

        Note that this method only scrapes images URLs, it doesn't
        download the images themselves. After calling scrape(),
        download() must be used to actually download the resources. It's
        not important to store the output of scrape() as the images URLs
        are saved within the object itself.

        Args:
            max_pages: the maximum number of pages to scrape URLs from.

        Returns:
            Set of string, each being the URL of an image. If scrape()
            is called twice, the sets are going to be different as
            MegaScraper() memorizes what URLs have been returned before.
        """
        assert isinstance(max_pages, int)
        assert max_pages >= 1
        num_pages = 0
        images_urls = set()
        while self._unexplored:
            url = self._unexplored.pop()
            print('--Processing the following URL: {}'.format(url))
            html = requests.get(url).content
            soup = bs4.BeautifulSoup(html, features='html.parser')
            self._unexplored.update(self._extract_unexplored_pages(soup))
            if re.search(self._regex_pages, url):
                images_urls.update(self._extract_images_urls(soup))
            self._explored.add(url)
            num_pages += 1
            if num_pages == max_pages:
                break
        new_images_urls = images_urls.difference(self._images_urls)
        self._images_urls.update(images_urls)
        return new_images_urls

    def download(self, how_many: int = _DEFAULT_HOW_MANY) -> None:
        """Downloads the images from the URLs scraped via scrape().

        Args:
            how_many: how many images to download.
        """
        assert isinstance(how_many, int)
        if not os.path.exists(self._output_folderpath):
            os.makedirs(self._output_folderpath)
        for _ in range(how_many):
            images_to_download = self._images_urls.difference(self._downloaded)
            if not images_to_download:
                break
            image_url = images_to_download.pop()
            image = PIL.Image.open(requests.get(image_url, stream=True).raw)
            self._downloaded.add(image_url)
            if image.width >= self._min_width and image.height >= self._min_height:
                # Decides the name of the downloaded image.
                if self._output_naming == 'keep':
                    image_filename = image_url.split('/')[-1]
                elif self._output_naming == 'numerical':
                    image_filename = str(self._downloaded_idx) + '.jpg'
                # Decides the folder structure (if any) of the output.
                if self._output_structure == 'flat':
                    image_filepath = os.path.join(
                        self._output_folderpath, image_filename)
                elif self._output_structure == 'grouped':
                    image_foldername = str(
                        int(
                            (self._downloaded_idx - 1) / self._images_per_folder
                        ) + self._folder_initial_num
                    ).zfill(4)
                    image_folderpath = os.path.join(
                        self._output_folderpath, image_foldername)
                    if not os.path.exists(image_folderpath):
                        os.makedirs(image_folderpath)
                    image_filepath = os.path.join(image_folderpath, image_filename)
                # Finally, it saves the image.
                image.save(image_filepath)
                self._downloaded_idx += 1
                raw_message = '--The following image was downloaded successfully: {}'
                print(raw_message.format(image_url))
            else:
                raw_message = '--The following image was skipped because of its size: {}'
                print(raw_message.format(image_url))


def parse_args() -> argparse.Namespace:
    """Parses the arguments provided.

    Only relevant if MegaScraper is used via command-line interface. If
    you're importing mega_scraper.py to use it as a library feel free
    to ignore this function.

    For a description of the args, please see the docstring for MegaScraper().

    Returns:
        The args as a dict-like structure (Namespace).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', '-s', type=str, required=True)
    parser.add_argument('--regex_pages', '-rp', type=str, default=_DEFAULT_REGEX_PAGES)
    parser.add_argument('--regex_images', '-ri', type=str, default=_DEFAULT_REGEX_IMAGES)
    parser.add_argument('--min_width', '-mw', type=int, default=_DEFAULT_MIN_WIDTH)
    parser.add_argument('--min_height', '-mh', type=int, default=_DEFAULT_MIN_HEIGHT)
    parser.add_argument('--output_folderpath', '-of', type=str, default=_DEFAULT_OUTPUT_FOLDERPATH)
    parser.add_argument('--output_structure', '-os', type=str,
                        default=_DEFAULT_OUTPUT_STRUCTURE, choices=_OUTPUT_STRUCTURE_VALUES)
    parser.add_argument('--output_naming', '-on', type=str,
                        default=_DEFAULT_OUTPUT_NAMING, choices=_OUTPUT_NAMING_VALUES)
    parser.add_argument('--images_per_folder', '-if', type=int, default=_DEFAULT_IMAGES_PER_FOLDER)
    parser.add_argument('--folder_initial_num', '-fn', type=int,
                        default=_DEFAULT_FOLDER_INITIAL_NUM)
    parser.add_argument('--max_pages', '-mp', type=int, default=_DEFAULT_MAX_PAGES)
    parser.add_argument('--how_many', '-hm', type=int, default=_DEFAULT_HOW_MANY)

    return parser.parse_args()


def main():
    """Main for MegaScraper."""
    args = parse_args()
    scraper = MegaScraper(
        seed=args.seed,
        regex_pages=args.regex_pages,
        regex_images=args.regex_images,
        min_width=args.min_width,
        min_height=args.min_height,
        output_folderpath=args.output_folderpath,
        output_structure=args.output_structure,
        output_naming=args.output_naming,
        images_per_folder=args.images_per_folder,
        folder_initial_num=args.folder_initial_num)
    scraper.scrape(args.max_pages)
    scraper.download(args.how_many)


if __name__ == '__main__':
    main()
