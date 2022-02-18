from pymongo import MongoClient
from selenium.webdriver import Chrome, ChromeOptions
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from selenium.common.exceptions import SessionNotCreatedException, NoSuchElementException
from datetime import date


class HHParser:
    parser_options = ChromeOptions()

    def __init__(self, keyword, pages=40, minimal_salary=0):
        self.keyword = "+".join(keyword.split())
        self.pages = pages
        self._driver = self.initialize_driver()
        self._page = 0
        self._next_page = True
        self.minimal_salary = minimal_salary

    def get_html(self, page):
        return f"https://hh.ru/search/" \
                f"vacancy?area=1&fromSearchLine=true&text={self.keyword}" \
                f"&page={page}&hhtmFrom=vacancy_search_list"

    def _write_to_mongo(self, data):
        client = MongoClient()
        with client:
            db = client["hh_parcer"]
            mongo = db[f"{self.keyword}({date.today().strftime('%Y-%m-%d')})"]
            for vacancy in data:
                mongo.update_one(
                    {
                        "link": vacancy["link"]
                    },
                    {
                        "$set": {
                            "name": vacancy["name"],
                            "company": vacancy["company"],
                            "min_salary": vacancy["min_salary"],
                            "max_salary": vacancy["max_salary"],
                            "link": vacancy["link"]

                        },
                    },
                    upsert=True
                )

    @staticmethod
    def update_chromedriver():
        chromedriver_autoinstaller.install()

    def initialize_driver(self):
        print("Initializing parser..")
        driver_options = ChromeOptions()
        driver_options.headless = True
        try:
            driver = Chrome(options=driver_options)
        except SessionNotCreatedException:
            self.update_chromedriver()
            driver = Chrome(options=driver_options)
        return driver

    @staticmethod
    def parse_salary(salary):
        vacancy_min_salary, vacancy_max_salary = None, None
        salary_string = " ".join(salary)
        if "от" in salary_string:
            vacancy_min_salary = salary_string.split()[1]
            vacancy_max_salary = None
        elif "до" in salary_string:
            vacancy_max_salary = salary_string.split()[1]
            vacancy_min_salary = None
        return vacancy_min_salary, vacancy_max_salary

    def get_vacancies(self):
        print("Getting list of vacancies..")
        while self._next_page and self._page < self.pages:
            print(f"Page {self._page + 1}")
            self._driver.get(self.get_html(self._page))
            self._driver.implicitly_wait(2)
            pager = self._driver.find_element("class name", "pager")

            try:
                self._next_page = pager.find_element("tag name", "a")
            except NoSuchElementException:
                self._next_page = False

            vacancies = []
            vacancies_block = self._driver.find_element("class name", "vacancy-serp")
            vacancies_list = vacancies_block.find_elements_by_class_name("vacancy-serp-item")

            for vacancy in vacancies_list:
                vacancy_soup = BeautifulSoup(vacancy.get_attribute("innerHTML"), "lxml")
                try:
                    salary = vacancy_soup.find_all("span", {"class": "bloko-header-section-3"})[1].get_text()
                except IndexError:
                    salary = None

                name_block = vacancy_soup.find_all("span", {"class": "bloko-header-section-3"})[0]
                vacancy_name = name_block.find("a", {"class": "bloko-link"}).get_text()
                vacancy_link = name_block.find("a", {"class": "bloko-link"}).get("href")
                vacancy_company_block = vacancy_soup.find("div", {"class": "vacancy-serp-item__meta-info-company"})
                vacancy_company = vacancy_company_block.find("a").get_text()

                if salary is not None:
                    salary_list = [x.replace("\u202f", "").strip() for x in salary.split("–")]
                    if len(salary_list) > 1:
                        vacancy_min_salary = salary_list[0]
                        vacancy_max_salary = salary_list[1]
                    else:
                        vacancy_min_salary, vacancy_max_salary = self.parse_salary(salary_list)
                else:
                    vacancy_min_salary, vacancy_max_salary = None, None

                vac = {
                    "min_salary": vacancy_min_salary,
                    "max_salary": vacancy_max_salary,
                    "name": vacancy_name,
                    "company": vacancy_company,
                    "link": vacancy_link
                }
                if vacancy_min_salary is not None and int(vacancy_min_salary) >= self.minimal_salary:
                    print(
                        f"Vacancy:\n"
                        f"\tCompany: {vacancy_company}\n"
                        f"\tPosition: {vacancy_name}\n"
                        f"\tSalary: {vacancy_min_salary} - {vacancy_max_salary}\n"
                        f"\tLink: {vacancy_link}\n"
                    )

                vacancies.append(vac)
            self._write_to_mongo(vacancies)
            self._page += 1
        self._driver.close()


def main():
    parcer = HHParser(
        input("Enter keywords: "),
        int(input("Enter number of pages (leave this field empty, if you want to find all vacancies): ")),
        int(input("Enter minimal salary you desire(leave blank if you don't care): "))
    )
    parcer.get_vacancies()


if __name__ == "__main__":
    main()
