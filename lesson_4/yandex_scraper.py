import requests
from lxml.html import fromstring
import datetime
from pymongo import MongoClient


headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }

ROOT_URL = "https://yandex.ru/news"
NEWS_BLOCK = "//section[@aria-labelledby='top-heading']"
NEWS_ITEM = ".//div[contains(@class, 'mg-grid__item')]"
NEWS_LINK = ".//a[@class='mg-card__link']"
NEWS_FOOTER = ".//div[contains(@class, 'mg-card-source')]"
FOOTER_LINK = "//a[@class='mg-card__source-link']"
PUBLISH_DATE = "span[@class='mg-card-source__time']"


def get_hot_news():
    with MongoClient() as client:
        db = client.news_parcer
        collection = db.yandex_news

        resp = requests.Session()
        resp.headers.update(headers)
        main_page = resp.get(ROOT_URL)
        dom = fromstring(main_page.text)

        news_block = dom.xpath(NEWS_BLOCK)
        news_items = news_block[0].xpath(NEWS_ITEM)

        for item in news_items:
            news = {}
            link = item.xpath(NEWS_LINK)[0].get("href")
            title = item.xpath(NEWS_LINK)[0].text
            footer = item.xpath(NEWS_FOOTER)[0]
            source = footer.xpath(FOOTER_LINK)[0].text
            publish_date = datetime.datetime.strptime(f"{datetime.date.today()} {footer.xpath(PUBLISH_DATE)[0].text}",
                                                      "%Y-%m-%d %H:%M")
            news["link"] = link
            news["title"] = title
            news["source"] = source
            news["publish_date"] = publish_date

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
