import re
from pymongo import MongoClient


class JobParserPipeline:
    salary_pattern = re.compile(r"\d+ \d+")

    def parse_salary(self, raw_salary: str):
        currency_pattern = re.compile(r"(?P<currency>\D+) на руки") if raw_salary.endswith("на руки") else \
                           re.compile(r"(?P<currency>\D+)$")
        salary = {}
        salary_limits = re.findall(self.salary_pattern, raw_salary)
        currency = re.search(currency_pattern, raw_salary)
        if not salary_limits:
            return None
        if len(salary_limits) == 2:
            try:
                salary["min"], salary["max"], salary["currency"] = int(salary_limits[0].replace(" ", "")),\
                                                                   int(salary_limits[1].replace(" ", "")),\
                                                                   currency.group("currency").strip()
            except AttributeError:
                salary["min"], salary["max"], salary["currency"] = int(salary_limits[0].replace(" ", "")),\
                                                                   int(salary_limits[1].replace(" ", "")),\
                                                                   None
        else:
            if raw_salary.startswith("до"):
                salary["min"], salary["max"], salary["currency"] = None, int(salary_limits[0].replace(" ", "")),\
                                                                   currency.group("currency").strip()
            else:
                try:
                    salary["min"], salary["max"], salary["currency"] = int(salary_limits[0].replace(" ", "")), \
                                                                       None, currency.group("currency").strip()
                except AttributeError:
                    salary["min"], salary["max"], salary["currency"] = int(salary_limits[0].replace(" ", "")), \
                                                                       None, None
        return salary

    def process_item(self, item, spider):
        item["salary"] = self.parse_salary(item["salary"])
        with MongoClient() as client:
            db = client.news_parcer
            collection = db[spider.name]
            collection.update_one(
                {
                    "link": item["link"]
                },
                {
                    "$set": item
                },
                upsert=True
            )

            return item
