import requests
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from datetime import date


class HHParcer:
    URL = "https://hh.ru/search/vacancy?area=1&fromSearchLine=true&"

    def __init__(self, keywords: str, pages=float("+inf")):
        self.keywords = "+".join(keywords.split()) if len(keywords.split()) > 1 else keywords
        self.pages = pages
        self.page = 0
        self.next = True

    def get_url(self, page):
        return f"https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text={self.keywords}" \
                   f"&page={page}&hhtmFrom=vacancy_search_list"

    def page_check(self, page):
        print(self.page)
        return True if page.find("a", {"data-qa": "pager-next"}) else False

    def get_vac_list(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                          " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36"
        }
        r = requests.get(self.get_url(self.page), headers=headers)

        if not r.status_code == 200:
            return None
        soup = BeautifulSoup(r.text, features="lxml")
        self.next = self.page_check(soup)
        vac_list = soup.find_all("div", attrs={"class": "vacancy-serp-item"})
        return vac_list

    @staticmethod
    def encode_salary(number):
        enc_number = number.encode("ascii", "ignore")
        dec_number = enc_number.decode()
        return dec_number

    def parse_vac_list(self):
        data = {}
        while self.next or self.page <= self.pages:
            vac_list = self.get_vac_list()
            vacancies = []
            if vac_list:
                for vac in vac_list:
                    vacancy = {}
                    link = vac.find("a", {"class": "bloko-link"})
                    url = link.get("href")
                    name = link.get_text()
                    vacancy["name"] = name
                    site = urlparse(url).hostname
                    salary = vac.find("div", {"class": "vacancy-serp-item__sidebar"})
                    if salary:
                        salary = vac.find("div", {"class": "vacancy-serp-item__sidebar"}).get_text()
                        converted_salary = re.sub("[A-zА-я.]", "", salary)
                        upper = re.compile(r"^до\s(?P<salary>\d*\s\d*)\s")
                        bottom = re.compile(r"^от\s(?P<salary>\d*\s\d*)\s")
                        salary_upper = re.search(upper, salary)
                        salary_bottom = re.search(bottom, salary)
                        if salary_upper:
                            salary = self.encode_salary(salary_upper.group("salary"))
                            vacancy["Salary upper limit"] = salary
                        elif salary_bottom:
                            salary_bottom_pattern = re.compile(r"^от\s(?P<salary_bottom>\d*\s\d*)\sдо"
                                                               r"(?P<salary_upper>\d*\s\d*)")
                            salary = re.search(salary_bottom_pattern, salary)
                            if salary:
                                salary_final_bottom = self.encode_salary(salary_bottom.group("salary_bottom"))
                                salary_final_upper = self.encode_salary(salary_bottom.group("salary_upper"))
                                vacancy["Salary lower limit"] = salary_final_bottom
                                vacancy["Salary upper limit"] = salary_final_upper
                        elif not all(map(str.isdigit, converted_salary)):
                            print(converted_salary)
                            vacancy["salary lower limit"] = self.encode_salary(converted_salary.split("–")[0])
                            vacancy["salary upper limit"] = self.encode_salary(converted_salary.split("–")[1])
                        # elif
                    vacancy["url"] = url
                    vacancy["site"] = site
                    vacancies.append(vacancy)
                data[f"Page_{self.page}"] = vacancies
                self.page += 1
            else:
                return data
            self.next = False
        return data

    def vac_list_to_json(self):
        with open(f"hh_{self.keywords}_{date.today()}.json", "w", encoding="utf-8") as jf:
            vacancies = self.parse_vac_list()
            json.dump(vacancies, jf, indent=4)


def main():
    keywords = input("Enter space-separated keywords: ")

    try:
        parser = HHParcer(keywords,
                          int(input("Enter amount of pages to scan (blank if you want to scan all possible): ")))
    except ValueError:
        parser = HHParcer(keywords)

    parser.vac_list_to_json()


if __name__ == "__main__":
    main()
