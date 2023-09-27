from common import *

EXCLUDE_KEYWORDS = [
    # "/search/result",
    "usedcar/detail/",
    "usedcar/shop/",
    "inquiry",
    "/usedcar/ajax",
    "page"
    ]

class WebCrawler:
    def __init__(self, domain):
        name = "web_crawler"
        self.domain = domain
        self.logger = init_logger(name)
        self.driver = init_driver()
        cookie_names = ["favorite_cars", "passersby_recent_view", "passersby_incomplete_inquiry"]
        self.count = 0
        self.old_path_checked = self._read_csv(name)
        self.checked_path = []
        self.writer = init_csv_writer(name)
        self.driver.get(domain + "/recent_search")
        add_cookies(self.driver, cookie_names)
