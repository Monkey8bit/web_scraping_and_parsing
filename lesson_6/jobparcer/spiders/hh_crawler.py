import scrapy
from scrapy.http import TextResponse

import re

from web_scraping_and_parsing.lesson_6.jobparcer.items import JobParserItem

PATTERN = re.compile(r"\d+ \d+")


class HHSpider(scrapy.Spider):
    SEARCH_TEMPLATE = "https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text="
    name = "hh_spider"
    allowed_domains = ["hh.ru"]

    main_xpaths = {
        "vacancy_link": "//a[contains(@data-qa, 'vacancy-serp__vacancy-title')]",
        "next_url": "//a[@data-qa='pager-next']",
    }

    vacancy_page_xpaths = {
        "title": "//h1[@data-qa='vacancy-title']//text()",
        "company": "//div[@class='bloko-columns-row']"
                   "//div[@class='bloko-columns-row']"
                   "/div[contains(@class, 'bloko-column')]"
                   "/div[@class='vacancy-company-wrapper']"
                   "//span[@data-qa='bloko-header-2']//text()",
        "experience": "//span[@data-qa='vacancy-experience']//text()",
        "salary": "//div[@data-qa='vacancy-salary']//span[contains(@data-qa, 'vacancy-salary-compensation')]//text()",
    }

    def __init__(self, keywords: str):
        super().__init__()
        self.keywords = "+".join(keywords.split())
        start_url = self.SEARCH_TEMPLATE + self.keywords
        self.start_urls = [start_url]

    def parse(self, response: TextResponse, **kwargs):
        links = response.xpath(self.main_xpaths.get("vacancy_link"))

        for link in links:
            link_href = link.attrib.get("href")
            yield response.follow(link_href, callback=self.parse_item)

        try:
            next_url = response.xpath(self.main_xpaths.get("next_url")).attrib.get("href")
            if next_url:
                yield response.follow(next_url, callback=self.parse)
        except AttributeError:
            pass

    def parse_item(self, response: TextResponse):
        item = JobParserItem()

        for field, path in self.vacancy_page_xpaths.items():
            item[field] = " ".join(response.xpath(path).re(r"\w+"))
            item["link"] = response.url
            item["site"] = self.allowed_domains[0]

        yield item
