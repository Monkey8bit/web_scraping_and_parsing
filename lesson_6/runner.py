from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from jobparcer.spiders.hh_crawler import HHSpider
from jobparcer.spiders.sj_crawler import SJCrawler
from jobparcer import settings


if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    hh_keywords = input("Input keywords for search vacancies on HeadHunter: ")
    sj_keywords = input("Input keywords for search vacancies on SuperJob: ")

    hh_spider_init_kwargs = {
        "keywords": hh_keywords,
    }
    sj_spider_init_kwargs = {
        "keywords": sj_keywords,
    }

    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(HHSpider, **hh_spider_init_kwargs)
    process.crawl(SJCrawler, **sj_spider_init_kwargs)
    process.start()
