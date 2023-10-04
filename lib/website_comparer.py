import os
import re
import time
import csv
from difflib import HtmlDiff
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from PIL import Image
from bs4 import BeautifulSoup
from pathlib import Path
import pdb
from lib.common import *
from concurrent import futures

EXCLUDE_KEYWORDS = [
    # "/search/result",
    "usedcar/detail/",
    "usedcar/shop/",
    "inquiry",
    "/usedcar/ajax",
    # "usedcar/search_area/",
    # "usedcar/search_shashu/",
    # "search/shop/pref/",
    # "search_kodawari/pref/01",
    # "usedcar/search_price",
    "page",
    # "usedcar/area_top/",
    # "usedcar/topic/lowprice/",
    # "usedcar/topic/ecocar/",
    # "usedcar/topic/4wd/",
    # "feature/search",
    # "feature/eco_car",
    # "feature/low_price"
    ]

class WebsiteComparer:
    def __init__(self, domain1, domain2, csv_name, is_sp):
        self.logger = init_logger(csv_name)
        self.csv_name = csv_name
        self.count = 0
        self.domain1 = domain1
        self.domain2 = domain2
        self.driver1 = init_driver(is_sp=is_sp)
        self.driver2 = init_driver(is_sp=is_sp)
        # HEADER: 'Path', 'Folder name', 'Pass?', 'Website 1 urls', 'Website 2 urls', 'Exception'
        self.old_paths_checked = self._read_csv(csv_name)
        # init writer using to append new data to file after read all the old data.
        self.writer = init_csv_writer(csv_name)

        self.driver1.get(self.domain1 + "/favorites")
        self.driver2.get(self.domain2 + "/favorites")
        # cookie_names = ["favorite_cars", "passersby_recent_view", "passersby_incomplete_inquiry"]
        add_cookies(self.driver1, ["user_id_mb7"])
        add_cookies(self.driver2, ["user_id_mb8"])

    def count_folders(self, path):
        if not os.path.exists(path):
            return 0

        folders = os.listdir(path)
        return len([x for x in folders if os.path.isdir(os.path.join(path, x))])

    def reach_max_folder(self, path):
        sub_path = Path(path)
        root_path = Path(*sub_path.parts[:5])
        if self.count_folders(root_path) >= 15:
            return True
        while sub_path != root_path:
            folder_count = self.count_folders(sub_path)
            if folder_count >= 8:
                return True
            sub_path = sub_path.parent
        return False

    def get_html_and_urls(self, driver, url, num):
        driver.get(url)
        el = driver.find_element(By.TAG_NAME, 'body')
        ignore_els = self.ignore_els(url)
        time.sleep(1)
        website_page_paths = get_page_paths(driver)
        el.screenshot(f"screenshot{num}.png")
        website_html = self.get_prettified_html(driver, ignore_els)

        return [website_html, website_page_paths]

    def compare_single_page(self, path):
        urls = self.find_website_urls(path)
        if len(urls) != 0:
            return urls

        url1 = urljoin(self.domain1, path)
        url2 = urljoin(self.domain2, path)
        folder_name = f"data/{self.csv_name}{re.sub(r'[?#=&]', '/', path)}"
        split_folder = folder_name.split("/")
        name_removed = folder_name.rsplit('/', 1)[0]
        if len(split_folder) > 5 and self.reach_max_folder(name_removed):
            print(f"Next => Max Folder: {path}")
            return []

        self.count += 1
        self.logger.info(f"{self.count}: Start compare: {path}")
        os.makedirs(folder_name, exist_ok=True)
        try:
            with futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Đưa các nhiệm vụ vào thread pool
                future1 = executor.submit(self.get_html_and_urls, self.driver1, url1, 1)
                future2 = executor.submit(self.get_html_and_urls, self.driver2, url2, 2)

                # Chờ cả 2 nhiệm vụ được thực hiện xong
                futures.wait([future1, future2])

                # Lấy kết quả từ các nhiệm vụ
                website1_html, website1_page_urls = future1.result()
                website2_html, website2_page_urls = future2.result()

            image1 = Image.open("screenshot1.png")
            image2 = Image.open("screenshot2.png")

            # keys1 = self.get_global_key(website1_page_urls)
            # keys2 = self.get_global_key(website2_page_urls)

            # key_equal = self.compare_list(keys1, keys2)

            merge_imgs = self._append_images([image1, image2], aligment='top')
            merge_imgs.save(f"{folder_name}/sc.png")
            
            diff = HtmlDiff()
            content_diff = diff.make_file(website1_html.splitlines(), website2_html.splitlines(), context=True)
            if "No Differences Found" in content_diff:
                html_pass = True
                self.logger.info("    ----No differences found-----")
            else:
                html_pass = False
                with open(f"{folder_name}/diff.html", "w", encoding="utf-8") as file:
                    file.write(content_diff)
                self.logger.info("    ++++++++DIFF+++++++")

            self._write_to_csv([path, folder_name, html_pass, "\n".join(website1_page_urls), "\n".join(website2_page_urls), ''])

            return list(set(website1_page_urls + website2_page_urls))
        except WebDriverException as ex:
            self._write_to_csv([path, folder_name, '', '', '', ex, ''])
            self.logger.info(f"    Error: {ex}")
            return []

    def compare_multiple_pages(self, path):
        extend_paths = [
            '/usedcar/feature/top', #pc, sp
            '/usedcar/feature/search', #pc, sp
            '/usedcar/feature/low_price', #pc, sp
            '/usedcar/feature/eco_car', #pc, sp
            '/usedcar/feature/Seasonal/1', #pc, sp
            '/usedcar/feature/Seasonal/2', #pc, sp
            # '/usedcar/kcar', #sp
            # '/usedcar/shop/gcs211859002/stock', #sp
            '/usedcar/topic/carmodel', #pc
            '/usedcar/new_arrival_mail', #pc
            '/usedcar/new_arrival_line', #pc
            # '/usedcar/area_top/hokkaido',
            # '/usedcar/area_top/hokushinetsu',
            # '/usedcar/area_top/kansai',
            # '/usedcar/area_top/kanto',
            # '/usedcar/area_top/kyushu',
        ]
        remaining_paths = self.compare_single_page(path) +  extend_paths
        checked_paths = [path, '/usedcar/logout', '/usedcar/recent_search']
        while(remaining_paths):
            if self.count >= 5000:
                return
            current_path = remaining_paths.pop(0)
            if "/usedcar" not in current_path or any(keyword in current_path for keyword in EXCLUDE_KEYWORDS):
                continue

            if current_path in checked_paths:
                continue

            paths = self.compare_single_page(current_path)
            checked_paths.append(current_path)
            remaining_paths.extend(paths)
            print(f"Remaining urls left: {len(set(remaining_paths))}")
        self.logger.info(f"Remaining urls left: {len(set(remaining_paths))}")

    def find_website_urls(self, test_path):
        if test_path in self.old_paths_checked:
            return self.old_paths_checked[test_path]
        return []

    def get_prettified_html(self, driver, ignore_els):
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        elements = soup.select(", ".join(ignore_els))

        for element in elements:
            element.extract()

        self._remove_domain_from_links(soup, 'a', 'href')
        self._remove_domain_from_links(soup, 'form', 'action')
    
        return soup.body.prettify()
    
    def _remove_domain_from_links(self, soup, tag_name, attribute):
        for tag in soup.find_all(tag_name):
            attr_value = tag.get(attribute)
            if attr_value:
                new_value = urlparse(attr_value).path
                tag[attribute] = new_value

    def _read_csv(self, file_name):
        try:
            data = {}
            with open(f"data/{file_name}.csv", 'r') as file:
                reader = csv.reader(file)

                for row in reader:
                    data[row[0]] = row[3].split("\n") + row[4].split("\n")

            return data
        except FileNotFoundError:
            self.logger.info(f"File not found. New file created: data/{file_name}.csv")
            return {}

    def _write_to_csv(self, data):
        write_to_csv(self.writer, data)

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
 
    def compare_list(self, l1, l2):
        l1.sort()
        l2.sort()
        if (l1 == l2):
            return True
        return False

    def get_global_key(self, urls):
        keys = []
        for url in urls:
            if "usedcar/detail/" not in url and "usedcar/shop/" not in url:
                continue
            if 'stock' in url:
                url = url.split("/stock")[0]
            key = url.rsplit("/", 1)[1]
            keys.append(key)
        return keys

    def ignore_els(self, url):
        ignore_els = [
            '.image',
            'input[name="authenticity_token"]',
            '[id^="batBeacon"]',
            '.ls-is-cached',
            '.lazyloading',
            '.lazyloaded',
            '.box_new',
            '.recommend-list-sp',
            '#page-top',
            '#ajax-recommends',
            '.ranking_list',
            '.ranking-shop',
            'img',
            '.status__label-list',
            '.information_board_pickup',
            '.ranking-list-item',
            '.recommendation_item',
            'source', # diff in url source image
            '.heading-level-02.header-fixed', # diff in style opacity
            '.favorite_count',
            '.recommendation_box_list',
            'script',
            '.usedResultList_item', # pc
            '.resultModePhoto', #pc
            '#user_search',
            '.internal-links-list.cf', # recommend result
            '.table_shop_pickup', # information board - pc
            # '.information_board_pickup', # information board - sp - tmp
            '.btn_line', # login/logout button
        ]

        if "feature" in url or 'search/result' in url or 'detail' in url:
            ignore_els += ['.balloon_message', '.result-wrap', '.review_detail_slider']
        elif "area_top" in url or "gd_city" in url:
            ignore_els.append('#resultWrapper')
        elif "topic" in url:
            ignore_els += ['iframe', 'noscript', 'meta']
        return ignore_els
