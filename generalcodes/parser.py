import requests
import re
from bs4 import BeautifulSoup
from db.config import headers


def get_vacancies(query, area, pages=3):
    vacancies = []

    for page in range(pages):
        url = f"https://hh.ru/search/vacancy?text={query}&area={area}&page={page}"

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, "lxml")
        cards = soup.find_all("div", {"data-qa": "vacancy-serp__vacancy"})

        if not cards:
            break

        for card in cards:
            title_tag = card.find("a", {"data-qa": "serp-item__title"})
            if not title_tag:
                continue

            title = title_tag.text.strip()
            link = title_tag["href"]

            company_tag = card.find(
                "a",
                {"data-qa": "vacancy-serp__vacancy-employer"}
            )
            company = company_tag.text.strip() if company_tag else "Не указано"

            exp_tag = card.find(
                "span",
                attrs={
                    "data-qa": lambda x: x and x.startswith(
                        "vacancy-serp__vacancy-work-experience"
                    )
                }
            )
            experience = exp_tag.get_text(strip=True) if exp_tag else "Не указано"

            raw_salary = parse_salary(card)
            salary = normalize_salary(raw_salary)

            vacancies.append({
                "title": title,
                "url": link,
                "company": company,
                "experience": experience,
                "salary": salary
            })

    return vacancies

def parse_salary(card):
    salary_tag = card.find(
        "span",
        {"data-qa": "vacancy-serp__vacancy-compensation"}
    )

    text = None

    if salary_tag:
        text = salary_tag.get_text(strip=True)
    else:
        spans = card.find_all("span")
        for span in spans:
            t = span.get_text(strip=True)
            if "₽" in t or "$" in t or "€" in t:
                text = t
                break

    if not text:
        return None

    return text

def normalize_salary(raw_salary: str):
    if not raw_salary:
        return None

    currency = "RUB"
    if "$" in raw_salary:
        currency = "USD"
    elif "€" in raw_salary:
        currency = "EUR"

    numbers = re.findall(r"\d+", raw_salary.replace(" ", ""))

    if not numbers:
        return None

    salary_value = max(map(int, numbers))

    return f"{salary_value} {currency}"
