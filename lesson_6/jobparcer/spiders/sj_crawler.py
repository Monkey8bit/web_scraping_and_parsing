import scrapy
from scrapy.http import TextResponse

from web_scraping_and_parsing.lesson_6.jobparcer.items import JobParserItem


class SJCrawler(scrapy.Spider):
    SEARCH_TEMPLATE = "https://russia.superjob.ru/vacancy/search/?keywords="
    name = 'sj_crawler'
    allowed_domains = ['superjob.ru']

    main_xpaths = {
        "link": "//div[@class='f-test-search-result-item']"
                "//div[@class='_2g1F-']"
                "//div[contains(@class, '_1tH7S')]"
                "//a[contains(@class, '_6AfZ9')]",
        "next": "//a[@rel='next']",
    }

    vacancy_page_xpaths = {
        "title": "//h1[contains(@class, '_3sM6i')]//text()",
        "company": "//div[contains(@class, '_2X1PV') and contains(@class, 'Znz0d')]/span//text()",
        "salary": "//span[contains(@class, '_1OuF_') and contains(@class, 'ZON4b')]"
                  "/span[contains(@class, '_2Wp8I')]//text()",
    }

    def __init__(self, keywords: str):
        super().__init__()
        self.keywords = "%20".join(keywords.split())
        start_url = self.SEARCH_TEMPLATE + self.keywords
        self.start_urls = [start_url]

    def parse_item(self, response: TextResponse):
        item = JobParserItem()

        for field, path in self.vacancy_page_xpaths.items():
            item[field] = " ".join(response.xpath(path).re(r"\w+"))
            item["link"] = response.url
            item["site"] = self.allowed_domains[0]

        yield item

    def parse(self, response: TextResponse, **kwargs):
        links = response.xpath(self.main_xpaths.get("link"))

        for link in links:
            link_href = link.attrib.get("href")
            yield response.follow(link_href, callback=self.parse_item)
        try:
            next_url = response.xpath(self.main_xpaths.get("next")).attrib.get("href")
            if next_url:
                yield response.follow(next_url, callback=self.parse)
        except AttributeError:
            pass
