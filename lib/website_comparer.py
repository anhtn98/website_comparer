import os
import re
import time
import csv
from difflib import HtmlDiff
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from PIL import Image
# import random
from bs4 import BeautifulSoup
import yaml
# import pdb

EXCLUDE_KEYWORDS = ["/search/result", "usedcar/detail/", "usedcar/shop/", "inquiry", "/usedcar/ajax",
                    "usedcar/search_area/", "usedcar/search_shashu/", "search/shop/pref/",
                    "search_kodawari/pref/01", "usedcar/search_price", "page", "usedcar/area_top/",
                    "usedcar/topic/lowprice", "usedcar/topic/ecocar", "usedcar/topic/4wd",
                    "feature/search", "feature/eco_car", "feature/low_price"]

class WebsiteComparer:
    def __init__(self, domain1, domain2, csv_name):
        self.filter_paths = []
        self.checked_paths = []
        self.ignore_paths = []
        self.count = 0
        self.data_yml = yaml.safe_load(open("data_cookies.yml", "r"))
        self.domain1 = domain1
        self.domain2 = domain2
        self.driver1 = self._init_driver()
        self.driver2 = self._init_driver()
        self.csv_name = csv_name
        # HEADER: 'Path', 'Folder name', 'HTML Pass?', 'Website 1 urls', 'Website 2 urls', 'Exception'
        self.old_paths_checked = self._read_csv(csv_name)
        # init writer using to append new data to file after read all the old data.
        self.writer = self._init_csv_writer(csv_name)

        self.driver1.get("https://zigexn:zigexn2vn@kuruma-mb5.zigexn.vn/usedcar/favorites")
        self.driver2.get(self.domain2 + "/favorites")
        cookie_names = ["favorite_cars", "passersby_recent_view", "passersby_incomplete_inquiry"]
        self._add_cookies(self.driver1, cookie_names)
        self._add_cookies(self.driver2, cookie_names)

    def compare_single_page(self, path):
        urls = self.find_website_urls(path)
        if len(urls) != 0:
            print("Next", path)
            return urls
        self.count += 1
        print(self.count)
        url1 = self.domain1 + path
        url2 = self.domain2 + path

        folder_name = self.csv_name + re.sub(r"[?#=&]", "/", path)
 
        try:
            print("Start get", url1)
            self.driver1.get(url1)
            print("Start get", url2)
            self.driver2.get(url2)
            print("Get Done")

            el1 = self.driver1.find_element(By.TAG_NAME, 'body')
            el2 = self.driver2.find_element(By.TAG_NAME, 'body')
            time.sleep(1)
            # Get page URLs while wait ajax load data to take screenshot
            website1_page_urls = self.get_page_urls(self.driver1, url1)
            website2_page_urls = self.get_page_urls(self.driver2, url2)

            os.makedirs(f"data/{folder_name}", exist_ok=True)
            # Take screenshot for compare UI
            print("Take screenshot")
            el1.screenshot("screenshot1.png")
            el2.screenshot("screenshot2.png")

            image1 = Image.open("screenshot1.png")
            image2 = Image.open("screenshot2.png")

            merge_imgs = self._append_images([image1, image2], aligment='top')
            merge_imgs.save(f"data/{folder_name}/sc.png")

            # Check for differences in page content
            diff = HtmlDiff()
            website1_html = self.get_prettified_html(self.driver1)
            website2_html = self.get_prettified_html(self.driver2)
            content_diff = diff.make_file(website1_html.splitlines(), website2_html.splitlines(), context=True)
            if "No Differences Found" in content_diff:
                html_pass = True
                print("----No differences found-----")
            else:
                html_pass = False
                with open(f"data/{folder_name}/diff.html", "w", encoding="utf-8") as file:
                    file.write(content_diff)
                print(f"Content differences saved to {folder_name}/diff.html.")

            self._write_to_csv([path, folder_name, html_pass, "\n".join(website1_page_urls), "\n".join(website2_page_urls), ''])

            return website1_page_urls + website2_page_urls
        except WebDriverException as ex:
            self._write_to_csv([path, folder_name, '', '', '', ex])
            print("Error:", ex)
            return []

    def compare_multiple_pages(self, path):
        print("Start compare:", path)
        urls = self.compare_single_page(path)
        print("End compare:", path)
        new_paths = []
        for url in urls:
            if "/usedcar" not in url or any(keyword in url for keyword in EXCLUDE_KEYWORDS):
                self.ignore_paths.append(url)
                continue

            part = url.split("/usedcar")[1]
            if part == "":
                continue

            if part not in self.filter_paths:
                self.filter_paths.append(part)
                new_paths.append(part)

        for new_path in new_paths:
            if new_path in self.checked_paths:
                continue

            if self.count >= 20:
                return

            self.checked_paths.append(new_path)
            self.compare_multiple_pages(new_path)

    def save_page_urls(self, url, page_urls, filename):
        page_urls = list(set(page_urls))
        with open(filename, "w") as file:
            file.write(f"Page URLs for {url}:\n")
            for page_url in page_urls:
                file.write(page_url + "\n")
        print(f"Page URLs saved to {filename}.")
    
    def find_website_urls(self, test_path):
        if test_path in self.old_paths_checked:
            return self.old_paths_checked[test_path]
        return []

    def get_prettified_html(self, driver):
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
    
        elements = soup.select('input[name="authenticity_token"], [id^="batBeacon"], .ls-is-cached, .lazyloading, .lazyloaded, .recommend-list-sp')

        for element in elements:
            element.extract()
    
        return soup.body.prettify()

    def get_page_urls(self, driver, url):
        links = driver.find_elements(By.TAG_NAME, "a")

        page_urls = []
        for link in links:
            href = link.get_attribute("href")
            if href and not href.startswith("#"):
                page_url = urljoin(url, href)
                if page_url not in page_urls:
                    page_urls.append(page_url)

        return page_urls

    def _init_driver(self):
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.set_preference("general.useragent.override", user_agent)
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(375,812)
        driver.set_page_load_timeout(20)
        return driver

    def _read_csv(self, file_name):
        try:
            data = {}
            with open(f"data/{file_name}.csv", 'r') as file:
                reader = csv.reader(file)

                for row in reader:
                    data[row[0]] = row[3].split("\n") + row[4].split("\n")

            return data
        except Exception as ex:
            print(ex)
            return {}

    def _add_cookies(self, driver, names):
        for name in names:
            driver.add_cookie(self.data_yml[name])

    def _init_csv_writer(self, file_name):
        file = open(f"data/{file_name}.csv", 'a', newline='')
        writer = csv.writer(file)
        return writer

    def _write_to_csv(self, data):
        self.writer.writerow(data)

    def _append_images(self, images, direction='horizontal', bg_color=(255,255,255), aligment='center'):
        widths, heights = zip(*(i.size for i in images))

        if direction=='horizontal':
            new_width = sum(widths)
            new_height = max(heights)
        else:
            new_width = max(widths)
            new_height = sum(heights)

        new_im = Image.new('RGB', (new_width, new_height), color=bg_color)

        offset = 0
        for im in images:
            if direction=='horizontal':
                y = 0
                if aligment == 'center':
                    y = int((new_height - im.size[1])/2)
                elif aligment == 'bottom':
                    y = new_height - im.size[1]
                new_im.paste(im, (offset, y))
                offset += im.size[0]
            else:
                x = 0
                if aligment == 'center':
                    x = int((new_width - im.size[0])/2)
                elif aligment == 'right':
                    x = new_width - im.size[0]
                new_im.paste(im, (x, offset))
                offset += im.size[1]

        return new_im
