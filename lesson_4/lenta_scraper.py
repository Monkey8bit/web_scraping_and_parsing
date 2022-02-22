import requests
from lxml.html import fromstring
import datetime
from pymongo import MongoClient


ROOT_URL = "https://lenta.ru"
LENTA_TOPNEWS = ".//div[@class='topnews']"
NEWS_COLUMN = "./div[@class='topnews__column']"
NEWS_ITEM = "./a | ./*/a"
TITLE_PATH = ".//h3 | .//span"
PUBLISH_DATE_PATH = ".//time | .//time"
SOURCE = "lenta.ru"


def get_hot_news():
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    resp = requests.get(ROOT_URL, headers=headers)
    dom = fromstring(resp.text)
    top_news = dom.xpath(LENTA_TOPNEWS)
    news_columns = top_news[0].xpath(NEWS_COLUMN)
    with MongoClient() as client:
        db = client.news_parcer
        collection = db.lenta_ru
        for news in news_columns:
            news_column = news.xpath(NEWS_ITEM)
            for item in news_column:
                item_info = {}
                if not item.get("href").startswith("https"):
                    link = ROOT_URL + item.get("href")
                else:
                    link = item.get("href")
                title = item.xpath(TITLE_PATH)
                publish_date = datetime.datetime.strptime(f"{datetime.date.today()} "
                                                          f"{item.xpath(PUBLISH_DATE_PATH)[0].text}", "%Y-%m-%d %H:%M")
                item_info["source"] = SOURCE
                item_info["title"] = title[0].text
                item_info["link"] = link
                item_info["publish_date"] = publish_date
                expired_news = datetime.datetime.now() - datetime.timedelta(hours=24)
                collection.update_one(
                    {
                        "link": link
                    },
                    {"$set": item_info},
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
