import psycopg2
from db.config import db_config

def update_vacancies_db(parsed_vacancies):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM msod5.cities")
    cities = {name: id for id, name in cur.fetchall()}

    cur.execute("SELECT id, name FROM msod5.skills")
    skills = {name: id for id, name in cur.fetchall()}

    cur.execute("SELECT url FROM msod5.vacancies")
    db_urls = {row[0] for row in cur.fetchall()}

    parsed_urls = set()
    added = 0

    for v in parsed_vacancies:
        parsed_urls.add(v["url"])

        cur.execute("""
            INSERT INTO msod5.companies (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (v["company"],))

        cur.execute("SELECT id FROM msod5.companies WHERE name = %s", (v["company"],))
        company_id = cur.fetchone()[0]

        city_id = cities[v["city"]]

        if v["url"] not in db_urls:
            cur.execute("""
                INSERT INTO msod5.vacancies
                (title, city_id, company_id, experience, salary, category, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                v["title"],
                city_id,
                company_id,
                v["experience"],
                v.get("salary"),
                v["category"],
                v["url"]
            ))

            vacancy_id = cur.fetchone()[0]

            for skill in v["skills"]:
                cur.execute("""
                    INSERT INTO msod5.vacancy_skills (vacancy_id, skill_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (vacancy_id, skills[skill]))

            added += 1

    urls_to_delete = db_urls - parsed_urls
    deleted = 0

    if urls_to_delete:
        cur.execute("""
            SELECT id FROM msod5.vacancies
            WHERE url = ANY(%s)
        """, (list(urls_to_delete),))

        vacancy_ids = [row[0] for row in cur.fetchall()]

        if vacancy_ids:
            cur.execute("""
                DELETE FROM msod5.recommendations
                WHERE vacancy_id = ANY(%s)
            """, (vacancy_ids,))

        cur.execute("""
            DELETE FROM msod5.vacancies
            WHERE url = ANY(%s)
        """, (list(urls_to_delete),))

        deleted = len(urls_to_delete)

    conn.commit()
    cur.close()
    conn.close()

    print(f"Добавлено: {added}, Удалено: {deleted}")
