import scrapy


class JobParserItem(scrapy.Item):
    title = scrapy.Field()
    company = scrapy.Field()
    experience = scrapy.Field()
    salary = scrapy.Field()
    link = scrapy.Field()
    site = scrapy.Field()
    pass
