from concurrent.futures import ThreadPoolExecutor
from generalcodes.parser import get_vacancies
from db.db import update_vacancies_db
from db.config import cities, queries, queries_pro


def parse_one(city, area, query):
    vacancies = get_vacancies(query, area)
    result = []

    for v in vacancies:
        v["city"] = city
        v["query"] = query
        v["category"] = "professional" if query in queries_pro else "general"
        v["skills"] = [query] if query in queries_pro else []
        result.append(v)

    return result


def main():
    all_vacancies = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = [
            executor.submit(parse_one, city, area, query)
            for city, area in cities.items()
            for query in queries
        ]

        for task in tasks:
            all_vacancies.extend(task.result())

    print("Собрано:", len(all_vacancies))

    update_vacancies_db(all_vacancies)


if __name__ == "__main__":
    main()
