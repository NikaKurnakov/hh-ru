import requests
from pprint import pprint
from dotenv import load_dotenv
import os
from itertools import count
from tabulate import tabulate
from contextlib import suppress


def get_salary_calculation(payment_from, payment_to):
    if payment_from and payment_to:
        salary = (int(payment_from) + int(payment_to)) / 2
    elif payment_from:
        salary = payment_from * 1.2
    elif payment_to:
        salary = payment_to * 0.8
    else:
        salary = None
    return salary


def predict_rub_salary_hh(vacancies):
    predicted_salaries_hh = []

    for vacancy in vacancies:
        salary = vacancy.get('salary')
        if salary and salary.get('currency') == 'RUR':
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            salary_calculation = get_salary_calculation(salary_to, salary_from)
            if salary_calculation:
                predicted_salaries_hh.append(salary_calculation)

    return predicted_salaries_hh



def get_vacancies_hh(programming_languages, max_attempts=3, max_pages=None):
    hh_url = "https://api.hh.ru/vacancies"
    vacancies_hh = []
    params = {
        "text" : f"Программист {programming_languages}",
        "area" : "1",
        "cuurency" : "RUR"
    }
    for page in count(0):
        with suppress(requests.exceptions.HTTPError):
            response = requests.get(hh_url, params=params)
            params["page"] = page
            response.raise_for_status()
            response = response.json()
            vacancies_hh.extend(response.get("items", []))
            if page >= response['pages']:
                break
    return vacancies_hh


def get_vacancies_superjob(superjob_secret_key, programming_languages, max_attempts=3, max_pages=None):
    superjob_url = "https://api.superjob.ru/2.0/vacancies"
    headers = {
        "X-Api-App-Id" : superjob_secret_key
    }
    params = {
        "keyword" : f"Программист {programming_languages}",
        "town" : "Москва",
    }
    vacancies_sj = []
    for page in count(0):
        params['page'] = page
        response = requests.get(superjob_url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            if response.status_code == 400:
                print(f"Bad request occurred. Exiting pagination loop.")
                break
            else:
                raise ex
        response = response.json()
        vacancies_sj.extend(response.get('objects'))
        if not response.get('more'):
            break
    return vacancies_sj


def predict_rub_salary_for_superJob(vacancies):
    predicted_salaries_sj = []

    for vacancy in vacancies:
        payment_from = vacancy.get("payment_from")
        payment_to = vacancy.get("payment_to")
        salary_calculation = get_salary_calculation(payment_to, payment_from)
        if salary_calculation:
            predicted_salaries_sj.append(salary_calculation)

    return predicted_salaries_sj



def create_table(languages_rate, table_name):
    table_vacansies = []
    for lang, lang_stats in languages_rate.items():
        table_row = [
            lang,
            lang_stats['vacancies_found'],
            lang_stats['vacancies_processed'],
            f"{lang_stats['average_salary']:.2f}" if lang_stats['average_salary'] is not None else "None",
        ]
        table_vacansies.append(table_row)
    table = AsciiTable(full_table, table_name)
    return table


def make_superjob_languages_rate(superjob_secret_key, programming_languages):
    stats_sj = {}
    for lang in programming_languages:
        vacancies_sj = get_vacancies_superjob(superjob_secret_key, lang)
        total_vacancies_sj = vacancies_sj
        predicted_salaries_sj = [predict_rub_salary_for_superJob(vacancy) for vacancy in vacancies_sj]
        predicted_salaries_sj = [sj for sj in predicted_salaries_sj if sj]
        average_salary_sj = sum(predicted_salaries_sj) / len(predicted_salaries_sj) if predicted_salaries_sj else None
        stats_sj[lang] = {
            "vacancies_found": total_vacancies_sj,
            "vacancies_processed": len(predicted_salaries_sj),
            "average_salary": average_salary_sj,
        }
    return stats_sj


def make_headhunter_languages_rate(programming_languages):
    stats_hh = {}
    for lang in programming_languages:
        vacancies_hh = get_vacancies_hh(lang)
        total_vacancies_hh = vacancies_hh
        predicted_salaries_hh = [predict_rub_salary_hh(vacancy) for vacancy in vacancies_hh]
        predicted_salaries_hh = [hh for hh in predicted_salaries_hh if hh]
        average_salary_hh = sum(predicted_salaries_hh) / len(predicted_salaries_hh) if predicted_salaries_hh else None
        stats_hh[lang] = {
            "vacancies_found": total_vacancies_hh,
            "vacancies_processed": len(predicted_salaries_hh),
            "average_salary": average_salary_hh,
        }
    return stats_hh

def main():
    load_dotenv()
    superjob_secret_key = os.environ["SUPERJOB_SECRET_KEY"]
    programming_languages = [
        "Python",
        "JavaScript",
        "Java",
        "C++",
        "C#",
        "Ruby",
        "Go",
        "Swift",
        "Kotlin",
        "Rust",
    ]
    languages_rate_sj = make_superjob_languages_rate(superjob_secret_key, programming_languages)
    languages_rate_hh = make_headhunter_languages_rate(programming_languages)
    table_sj = create_table(languages_rate_sj, "SuperJob Moscow")
    table_hh = create_table(languages_rate_hh, "HeadHunter Moscow")
    print(f"{table_sj.table}\n\n{table_hh.table}")



if __name__ == "__main__":
    main()



