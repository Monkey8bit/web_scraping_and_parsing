from pymongo import MongoClient
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    SessionNotCreatedException,
    NoSuchElementException,
    ElementClickInterceptedException,

)
from urllib.parse import urljoin
import re


class VKParser:
    ROOT_URL = "https://vk.com"
    IMAGE_PATTERN = re.compile(r"url\((?P<url>.+)\)")
    OPTIONS = ChromeOptions()
    OPTIONS.headless = True
    DEFAULT_GROUP = "tokyofashion"

    def __init__(self, keyword, group="tokyofashion"):
        self.keyword = keyword
        self.group = group if group else self.DEFAULT_GROUP
        self.group_link = urljoin(self.ROOT_URL, self.group)

    @staticmethod
    def _write_to_mongo(data):
        print("Writing data to database..")
        with MongoClient() as client:
            db = client.news_parcer
            collection = db.vk_posts
            for document in data:
                collection.update_one(
                    {
                        "_id": document["id"]
                    },
                    {
                        "$set": document
                    },
                    upsert=True
                )

    def parse_posts(self, raw_posts):
        i = 1
        posts = []
        print("Retrieving data..")
        for post in raw_posts:
            print(f"Post {i} of {len(raw_posts)}")
            new_post = {}
            post_id = post.get_attribute("id")
            post_dom = BeautifulSoup(post.get_attribute("innerHTML"), "lxml")
            posted = post_dom.find("span", {"class": "rel_date"}).text
            try:
                content = post_dom.find("div", {"class": "wall_post_text"}).text
            except AttributeError:
                content = None
            post_partial_url = post_dom.find("a", {"class": "post_link"}).get("href")
            post_link = urljoin(self.group_link, post_partial_url)
            post_likes = post_dom.find("span", {"class": "_counter_anim_container"}).text
            post_reposts = post_dom.find("div", {"class": "_share"}).get("data-count")

            try:
                post_views = int(post_dom.find("div", {"class": "like_views"}).get("title").split()[0])
            except AttributeError:
                post_views = None

            try:
                post_images = post_dom.find("div", {"class": "page_post_sized_thumbs"})
                images = post_images.find_all("a", {"class": "image_cover"})
                image_list = []
                for image in images:
                    image_url_finder = re.search(self.IMAGE_PATTERN, image.get("style"))
                    image_url = image_url_finder.group("url")
                    image_list.append(image_url)
            except NoSuchElementException:
                image_list = None

            new_post["id"] = post_id
            new_post["posted_time"] = posted
            new_post["content"] = content
            new_post["link"] = post_link
            new_post["likes"] = post_likes
            new_post["reposts"] = post_reposts
            new_post["views"] = post_views
            new_post["used_images"] = image_list
            posts.append(new_post)

            i += 1

        return posts

    def get_posts(self):
        print("Initializing driver..")
        try:
            driver = Chrome(options=self.OPTIONS)
        except SessionNotCreatedException:
            chromedriver_autoinstaller.install()
            driver = Chrome(options=self.OPTIONS)

        driver.get(self.group_link)
        driver.implicitly_wait(1)
        try:
            search_button = driver.find_element_by_class_name("ui_tab_search")
        except NoSuchElementException:
            search_button = None
            print(f"Can't find group {self.group_link}")
            exit(0)

        try:
            search_button.click()
        except ElementClickInterceptedException:
            footer = driver.find_element_by_id("page_bottom_banners_root")
            driver.execute_script("arguments[0].style.display = 'none';", footer)
            driver.execute_script("window.scrollTo(0,500)")
            search_button.click()

        search_input = driver.find_element_by_class_name("ui_search_field")
        search_input.send_keys(self.keyword)
        search_input.send_keys(Keys.ENTER)
        driver.implicitly_wait(2)
        current_height = driver.execute_script("return document.body.scrollHeight")

        print("Loading DOM..")

        while True:
            not_now_button = driver.find_elements_by_class_name("JoinForm__notNowLink")
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            driver.implicitly_wait(3)

            if not_now_button:
                not_now_button = driver.find_elements_by_class_name("JoinForm__notNowLink")[0]
                not_now_button.click()
                continue

            new_height = driver.execute_script("return document.body.scrollHeight")
            driver.implicitly_wait(3)
            if current_height == new_height:
                break
            current_height = new_height

        search_posts = driver.find_element_by_id("page_search_posts")
        new_posts = search_posts.find_elements_by_class_name("post")
        if not new_posts:
            print(f"There is no posts with keyword '{self.keyword}'")
            exit(0)
        print(f"Find {len(new_posts)} posts with keyword '{self.keyword}'")
        posts = self.parse_posts(new_posts)
        self._write_to_mongo(posts)


def main():
    parcer = VKParser(
        input("Enter keywords for search in group (default group - tokyofashion): "),
        input("For search in specific group, enter link to that group without 'https://vk.com': ")
    )
    parcer.get_posts()


if __name__ == "__main__":
    main()
