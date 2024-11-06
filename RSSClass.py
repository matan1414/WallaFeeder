import logging
import Enums
import re
from bs4 import BeautifulSoup
#from seleniumbase import Driver
import time


class RSSObject:
    def __init__(self):
        self.title = ''
        self.id = ''
        self.url = ''
        self.published_date = ''
        self.description = ''
        self.image_url = ''


class RSSClass:
    rss_object = RSSObject()

    def __init__(self, _logger):
        self.logger = _logger


    def print_class(self):
        object_members = (f'Title: {self.rss_object.title}'
                          f'\nID: {self.rss_object.id}'
                          f'\nDescription: {self.rss_object.description}'
                          f'\nImage URL: {self.rss_object.image_url}'
                          f'\nPublished Date: {self.rss_object.published_date}'
                          f'\n\nURL -> {self.rss_object.url}')
        return object_members


    def is_new_entry(self, entry_id, category):
        last_id = getattr(Enums.LastEntriesIDs, category, None)
        if entry_id != last_id:
            setattr(Enums.LastEntriesIDs, category, entry_id)
            return True

    def extract_id(self, url):
        # Use regular expression to find the first contiguous sequence of digits
        match = re.search(r'\d+', url)
        return match.group(0) if match else None
