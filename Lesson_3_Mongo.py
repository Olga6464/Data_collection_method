#1.Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать
#функцию, записывающую собранные вакансии в созданную БД.
#2.Написать функцию, которая производит поиск и выводит на экран вакансии с
#заработной платой больше введённой суммы.
#3.Написать функцию, которая будет добавлять в вашу базу данных только
#новые вакансии с сайта.

from bs4 import BeautifulSoup as bs
import requests
from pprint import pprint
from pymongo import MongoClient
import pandas as pd
import re

client = MongoClient ('127.0.0.1', 27017)
db = client['hh_db']

##https://hh.ru/search/vacancy?clusters=true&enable_snippets=true&selary=&st=searchVacancy&text=QA
prof = 'QA'
# Вакансия QA

main_link = 'https://hh.ru'
params = {'clusters': 'true',
          'enable_snippets': 'true',
          'salary': ' ',
          'st': 'searchVacancy',
          'text': prof #,
        }  # передадим параметры в словарик

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'}
response = requests.get(main_link + '/search/vacancy/',params=params,headers=headers)

if response.status_code != 200:
    print(f' {response.status_code}')
else:
    dom = bs(response.text, 'html.parser')
    page_block = dom.find('div', {'data-qa': 'pager-block'})
    if not page_block:
        last_page = 1
    else:
        last_page = int(page_block.find_all('a', {'class': 'HH-Pager-Control'})[-2].getText())
        print(f'last_page {last_page}')
    total_y = 0
    total_n = 0
    for page in range(0, last_page):
        params['page'] = page
        response = requests.get(main_link + '/search/vacancy/', params=params, headers=headers)
        dom = bs(response.text, 'html.parser')
        vacancy_list = dom.find_all('div', {'class': 'vacancy-serp-item'})
        if len(vacancy_list) == 0:
            print(f'Vacancies with QA "{prof}" ')
        else:
            vacancies = []
            y = 0
            n = 0
            for vacancy in vacancy_list:
                vacancy_data = {}
                vacancy_name_block = vacancy.find('a', {'class': 'bloko-link HH-LinkModifier'})
                vacancy_name = vacancy_name_block.getText()
                vacancy_link = vacancy_name_block['href']
                company_name = vacancy.find('div', {'class': 'vacancy-serp-item__meta-info'}) \
                                     .find('a') \
                                     .getText()
                city = vacancy.find('span', {'class': 'vacancy-serp-item__meta-info'}) \
                              .getText() \
                              .split(', ')[0]
                metro = vacancy.find('span', {'class': 'vacancy-serp-item__meta-info'}).findChild()
                if not metro:
                    metro = None
                else:
                    metro = metro.getText()

                salary = vacancy.find('div', {'class': 'vacancy-serp-item__compensation'})
                if not salary:
                    salary_min = None
                    salary_max = None
                    salary_currency = None
                else:
                    salary = salary.getText().replace(u'\xa0', u' ')

                    salary = re.split(r'\s|-', salary)

                    if salary[0] == 'до':
                        salary_min = None
                        salary_max = int(salary[1])
                    elif salary[0] == 'от':
                        salary_min = int(salary[1])
                        salary_max = None
                    else:
                        salary_min = int(salary[0])
                        salary_max = int(salary[1])

                    salary_currency = salary[2]


                vacancy_data['vacancy_name'] = vacancy_name
                vacancy_data['company_name'] = company_name
                vacancy_data['city'] = city
                vacancy_data['metro'] = metro
                vacancy_data['salary_min'] = salary_min
                vacancy_data['salary_max'] = salary_max
                vacancy_data['salary_currency'] = salary_currency
                vacancy_data['vacancy_link'] = vacancy_link
                for old_vacancy in db.vacancies.find({'vacancy_link': vacancy_link}):
                    n += 1
                    break
                else:
                    db.vacancies.insert_one(vacancy_data)
                    y += 1
                    #    vacancies.append(vacancy_data)
                total_y += y
                total_n += n
        print(f'New vacancies were added: {total_y}, reentry cancelled: {total_n}')

# Значение минимально зарплаты
maxsalary = 100000

for vacancy in vacancies.find({'$or': [{'salary_max': {'$gt': maxsalary}}, {'salary_min': {'$gt': maxsalary}}]}):
     pprint(vacancy)



