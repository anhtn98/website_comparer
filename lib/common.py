from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import logging
import os
import csv
import yaml
import pdb

def get_page_paths(driver):
    links = driver.find_elements(By.TAG_NAME, "a")

    page_paths = []
    for link in links:
        href = link.get_attribute("href")
        if href and not href.startswith("#") and "usedcar" in href:
            path = urlparse(href).path
            if path not in page_paths:
                page_paths.append(path)

    return page_paths

def init_driver(is_sp = True):
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    if is_sp:
        options.set_preference("general.useragent.override", user_agent)

    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(40)

    if is_sp:
        driver.set_window_size(375,812)

    return driver

def init_logger(log_file_name):
    logger = logging.getLogger(__name__)

    # Cấu hình logging
    logger.setLevel(logging.INFO)
    # Kiểm tra nếu file log không tồn tại, tạo mới file
    log_path = f'log/{log_file_name}.log' 
    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            pass
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def init_csv_writer(file_name):
    file = open(f"data/{file_name}.csv", 'a', newline='')
    writer = csv.writer(file)
    return writer

def write_to_csv(writer, data):
    writer.writerow(data)

def add_cookies(driver, names):
    cookies = yaml.safe_load(open("data_cookies.yml", "r"))
    for name in names:
        driver.add_cookie(cookies[name])
