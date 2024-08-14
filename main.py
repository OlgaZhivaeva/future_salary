import requests
import time
from environs import Env
from statistics import mean
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if not salary_from:
        return int(salary_to * 1.2)
    if not salary_to:
        return int(salary_from * 0.8)
    return int((salary_from + salary_to) / 2)


def predict_rub_salary_hh(vacancy):
    if not vacancy['salary']:
        return None
    if vacancy['salary']['currency'] != 'RUR':
        return None
    return predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])


def predict_rub_salary_for_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    if not (vacancy['payment_from'] or vacancy['payment_from']):
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_statistics_for_hh(languages):
    statistics = {}
    for language in languages:
        salaries = []
        page = 0
        pages_number = 101
        id_of_Moscow = 1
        last_30_days = 30

        while page < pages_number:
            params = {
                'text': f'Программист {language}',
                'area': id_of_Moscow,
                'period': last_30_days,
                'page': page
            }

            response = requests.get(url='https://api.hh.ru/vacancies/', params=params)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                page += 1
                time.sleep(0.5)
                continue
            vacancies = response.json()
            pages_number = vacancies['pages']
            page += 1
            time.sleep(0.5)

            for vacancy in vacancies['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    salaries.append(salary)

        statistics[language] = {
            'vacancies_processed': len(salaries),
            'average_salary': '-' if not salaries else int(mean(salaries)),
            'vacancies_found': vacancies['found']
        }

    return statistics


def get_statistics_for_sj(languages, secret_key):
    statistics = {}
    for language in languages:
        salaries = []
        page = 0
        more = True
        programming_development = 48
        id_of_Moscow = 4
        for_all_time = 0

        while more:
            headers = {
                'X-Api-App-Id': secret_key
            }
            params = {
                'keyword': language,
                'catalogues': programming_development,
                'town': id_of_Moscow,
                'page': page,
                'period': for_all_time
            }
            response = requests.get('https://api.superjob.ru/2.0/vacancies/',
                                    headers=headers, params=params)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                page += 1
                time.sleep(0.5)
                continue
            vacancies = response.json()
            more = vacancies['more']
            for vacancy in vacancies['objects']:
                salary = predict_rub_salary_for_sj(vacancy)
                if salary:
                    salaries.append(salary)
            page += 1
            time.sleep(0.5)

        statistics[language] = {
            'vacancies_processed': len(salaries),
            'average_salary': '-' if not salaries else int(mean(salaries)),
            'vacancies_found': vacancies['total']
        }

    return statistics


def get_statistics_table(statistics, title):
    statistics_table = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]
    for language, vacancies in statistics.items():
        statistics_table.append([
            language,
            vacancies['vacancies_found'],
            vacancies['vacancies_processed'],
            vacancies['average_salary'],
        ])
    output_table = AsciiTable(statistics_table, title)
    return output_table.table


def main():
    env = Env()
    env.read_env()
    secret_key = env.str('SECRET_KEY')
    languages = ['C#', 'Objective-C', 'Ruby', 'Java', 'C', 'TypeScript',
                 'Scala', 'Go', 'Swift', 'C++', 'PHP', 'JavaScript', 'Python']

    statistics = get_statistics_for_hh(languages)
    title = 'HeadHunter Moscow'
    statistics_table = get_statistics_table(statistics, title)
    print(statistics_table)

    statistics = get_statistics_for_sj(languages, secret_key)
    title = 'SuperJob Moscow'
    statistics_table = get_statistics_table(statistics, title)
    print()
    print(statistics_table)


if __name__ == "__main__":
    main()
