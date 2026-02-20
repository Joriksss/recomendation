import psycopg2

def update_vacancies_db(parsed_vacancies):
    conn = psycopg2.connect(
        host="89.223.65.229",
        port=5432,
        database="msod_database",
        user="big_data_engineer",
        password="H4d00p_Spark$"
    )

    cur = conn.cursor()

    cur.execute("SELECT url FROM msod5.vacancies")
    db_urls = {row[0] for row in cur.fetchall()}

    parsed_urls = set()

    for v in parsed_vacancies:
        parsed_urls.add(v["url"])

        if v["url"] not in db_urls:
            cur.execute("""
            INSERT INTO msod5.vacancies
            (title, city, query, experience, salary, url, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                v["title"],
                v["city"],
                v["query"],
                v["experience"],
                v.get("salary"),
                v["url"],
                v["category"]
            ))
    urls_to_delete = db_urls - parsed_urls

    if urls_to_delete:
        cur.execute(
            "DELETE FROM msod5.vacancies WHERE url = ANY(%s)",
            (list(urls_to_delete),)
        )

    conn.commit()
    cur.close()
    conn.close()
