import requests
from lxml.html import fromstring
import datetime
from pymongo import MongoClient
from dateutil import parser


headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
ROOT_URL = "https://news.mail.ru/"
NEWSBLOCK_PATH = "//table[@class='daynews__inner']"
MAIN_NEWS = ".//div[contains(@class, 'daynews__item')]/a"
NEWS_LIST = "//ul[contains(@class, 'list_half')]"
NEWS_LIST_ITEM = "./li[@class='list__item']/a"
INFO_BLOCK = "//div[contains(@class, 'cols__inner')]/div[contains(@class, 'js-article')]"
LINK_TO_DATE = ".//span[contains(@class, 'js-ago')]"
LINK_TO_SOURCE = ".//span[@class='link__text']"
LINK_TO_TITLE = ".//h1[@class='hdr__inner']"


def get_hot_news():
    resp = requests.Session()
    resp.headers.update(headers)
    main_page = resp.get(ROOT_URL)
    dom = fromstring(main_page.text)
    news_block = dom.xpath(NEWSBLOCK_PATH)
    news_list = dom.xpath(NEWS_LIST)
    news_links = []
    main_news = news_block[0].xpath(MAIN_NEWS)
    news_from_list = news_list[0].xpath(NEWS_LIST_ITEM)

    for item in main_news:
        news_links.append(item.get("href"))

    for item in news_from_list:
        news_links.append(item.get("href"))

    with MongoClient() as client:
        db = client.news_parcer
        collection = db.mail_ru_news
        for link in news_links:
            news = {}
            news_page = resp.get(link)
            page_dom = fromstring(news_page.text)
            info_block = page_dom.xpath(INFO_BLOCK)[0]
            publish_date = str(parser.parse(info_block.xpath(LINK_TO_DATE)[0].get("datetime")))
            source = info_block.xpath(LINK_TO_SOURCE)[0].text
            title = info_block.xpath(LINK_TO_TITLE)[0].text
            news["title"] = title
            news["publish_date"] = publish_date
            news["source"] = source
            news["link"] = link
            expired_news = datetime.datetime.now() - datetime.timedelta(hours=24)

            collection.update_one(
                {
                    "link": link
                },
                {"$set": news},
                upsert=True
            )
            collection.delete_many(
                {
                    "publish_date": {"$lt": expired_news}
                }
            )


def main():
    get_hot_news()


if __name__ == "__main__":
    main()
