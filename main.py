import requests
from dotenv import load_dotenv
import os
from terminaltables import AsciiTable
from itertools import count
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


def get_vacancies_hh(programming_languages):
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


def predict_rub_salary_hh(vacancies_hh):
    total_salary = 0
    vacancies_count = 0
    for vacancy in vacancies_hh:
        salary_from = vacancy.get("payment_from")
        salary_to = vacancy.get("payment_to")
        salary = get_salary_calculation(salary_from, salary_to)
        if salary:
            total_salary += salary
            vacancies_count += 1
    average_salary = 0
    if vacancies_count:
        average_salary = total_salary / vacancies_count
    return vacancies_count, average_salary


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
        response = requests.get(superjob_url, headers=headers, params=params, timeout=60)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            if response.status_code == 400:
                print(f"Bad request occurred. Exiting pagination loop.")
                break
            else:
                raise ex
        response = response.json()
        response_data = response.get('objects')
        for response in response_data:
            vacancies_sj.extend(response)
            if not response.get('more'):
                break
    return vacancies_sj


def predict_rub_salary_for_superJob(vacancies_sj):
    total_salary = 0
    vacancies_count = 0
    for vacancy in vacancies_sj:
        salary_from = vacancy.get("payment_from")
        salary_to = vacancy.get("payment_to")
        salary = get_salary_calculation(salary_from, salary_to)
        if salary:
            total_salary += salary
            vacancies_count += 1
    average_salary = 0
    if vacancies_count:
        average_salary = total_salary / vacancies_count
    return vacancies_count, average_salary



def create_table(languages_rate, table_name):
    full_table = [["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]]
    for language, content in languages_rate.items():
        table_params = [
            language, content["vacancies_found"], content["vacancies_processed"], content["average_salary"]
        ]
        full_table.append(table_params)
    table = AsciiTable(full_table, table_name)
    return table


def make_superjob_languages_rate(superjob_secret_key, programming_languages):
    stats_sj = {}
    for lang in programming_languages:
        vacancies_sj = get_vacancies_superjob(superjob_secret_key, lang)
        total_vacancies_sj = vacancies_sj
        # print(type(total_vacancies_sj))
        predicted_salaries_sj = [predict_rub_salary_for_superJob(vacancy) for vacancy in vacancies_sj if isinstance(vacancy, dict)]
        predicted_salaries_sj = [salary for salary in predicted_salaries_sj if salary]
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
        predicted_salaries_hh = [salary for salary in predicted_salaries_hh if salary]
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


