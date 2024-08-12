import requests
import time
from environs import Env
from statistics import mean
from pprint import pprint


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
    if not vacancy['payment_from'] & vacancy['payment_from']:
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_statistics_for_hh(languages):
    statistics = {}
    for language in languages:
        salaries = []
        page = 0
        pages_number = 101

        while page < pages_number:
            params = {
                'text': f'Программист {language}',
                'area': 1,
                'period': 30,
                'page': page
            }

            response = requests.get(url='https://api.hh.ru/vacancies/', params=params)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                page += 1
                time.sleep(0.5)
                continue
            json_vacancies = response.json()
            pages_number = json_vacancies['pages']
            page += 1
            time.sleep(0.5)

            for vacancy in json_vacancies['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    salaries.append(salary)
        if salaries:
            statistics[language] = {}
            statistics[language]['vacancies_processed'] = len(salaries)
            statistics[language]['average_salary'] = int(mean(salaries))
            statistics[language]['vacancies_found'] = json_vacancies['found']

    return statistics


def get_statistics_for_sj(languages, secret_key):
    statistics = {}
    for language in languages:
        salaries = []
        page = 0
        more = True

        while more:
            headers = {
                'X-Api-App-Id': secret_key
            }
            params = {
                'keyword': language,
                'catalogues': 48,
                'town': 4,
                'page': page,
                'count': 20,
                'period': 0
            }
            response = requests.get('https://api.superjob.ru/2.0/vacancies/',
                                    headers=headers, params=params)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                page += 1
                time.sleep(0.5)
                continue
            json_vacancies = response.json()
            more = json_vacancies['more']
            for vacancy in json_vacancies['objects']:
                salary = predict_rub_salary_for_sj(vacancy)
                if salary:
                    salaries.append(salary)
            page += 1
            time.sleep(0.5)

        if salaries:
            statistics[language] = {}
            statistics[language]['vacancies_processed'] = len(salaries)
            statistics[language]['average_salary'] = int(mean(salaries))
            statistics[language]['vacancies_found'] = json_vacancies['total']

    return statistics


def main():
    env = Env()
    env.read_env()
    secret_key = env.str('SECRET_KEY')
    languages = ['C#', 'Objective-C', 'Ruby', 'Java', 'C', 'TypeScript',
                 'Scala','Go', 'Swift', 'C++', 'PHP', 'JavaScript', 'Python']
    pprint(get_statistics_for_hh(languages))
    pprint(get_statistics_for_sj(languages, secret_key))



if __name__ == "__main__":
    main()
