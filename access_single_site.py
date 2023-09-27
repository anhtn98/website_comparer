import requests
from bs4 import BeautifulSoup
import time
import csv
from urllib.parse import urljoin
from lib.common import init_logger

EXCLUDE_KEYWORD = [
    'usedcar/detail/',
    'usedcar/shop/',
    'inquiry',
    'usedcar/ajax',
    'page'
]
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"


class CrawlAll:
    def __init__(self):
        self.domain = "https://kuruma-mb8.zigexn.vn/usedcar"
        self.old_data = self._read_old_data()
        self.writer = self._init_csv_writer()
        self.count = 0
        self.search_result_count = 0
        self.logger = init_logger("all_urls")

    def crawl_website(self):
        start = time.time()
        remaining_urls = self.send_request_and_get_urls(self.domain)
        checked_urls = [self.domain]
        self.count += 1
        while (remaining_urls):
            if self.count >= 20000:
                break
            current_url = remaining_urls.pop(0)
            if current_url in checked_urls:
                # self.logger.info(f"Next {current_url}")
                continue
            
            if 'search/result' in current_url:
                self.search_result_count += 1
                if self.search_result_count >= 10000:
                    # self.logger.info("Reach max search result")
                    continue
            urls = self.send_request_and_get_urls(current_url)
            checked_urls.append(current_url)
            remaining_urls.extend(urls)
            self.logger.info(f"Remaining urls left: {len(set(remaining_urls))}")

        self.logger.info(f"Remaining urls left: {len(set(remaining_urls))}")
        h, m, s = elapsed_time_from(start)
        self.logger.info(f"Elapsed time: {h} giờ {m} phút {s} giây")


    def send_request_and_get_urls(self, url):
        urls = self.find_website_urls(url)
        if len(urls) != 0:
            return urls
        self.count += 1
        self.logger.info(f"{self.count} - Checking: {url}")

        try:
            response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=40)
            status_code = response.status_code
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = self.get_page_urls(soup)
            self.write_to_csv([url, status_code, "\n".join(urls)])
            return urls
        except Exception as ex:
            self.write_to_csv([url, ex, ''])
            self.logger.info(f"Error {ex}")
            return []

    def get_page_urls(self, soup):
        links = soup.find_all("a")
        page_urls = []
        for link in links:
            href = link.get('href')
            if href and not href.startswith("#"):
                page_url = urljoin(self.domain, href)
                if 'usedcar' not in page_url or any(keyword in page_url for keyword in EXCLUDE_KEYWORD):
                    continue

                if page_url not in page_urls:
                    page_urls.append(page_url)
        return page_urls

    def _init_csv_writer(self):
        file = open("all_urls.csv", 'a', newline='')
        writer = csv.writer(file)
        return writer

    def _read_old_data(self):
        try:
            data = {}
            with open('all_urls.csv', 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    data[row[0]] = row[2].split("\n")
            return data
        except FileNotFoundError:
            self.logger.info("File Not Found")
            return {}

    def write_to_csv(self, data):
        self.writer.writerow(data)

    def find_website_urls(self, test_url):
        if test_url in self.old_data:
            return self.old_data[test_url]
        return []

def elapsed_time_from(start_time):
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    return [hours, minutes, seconds]


crawler = CrawlAll()
crawler.crawl_website()
