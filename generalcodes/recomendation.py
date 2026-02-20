import psycopg2
from db.config import db_config

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def recommend_vacancies(user_id: int, limit=10):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute(
        "SELECT city_id FROM msod5.users WHERE id = %s",
        (user_id,)
    )
    row = cur.fetchone()
    user_city = row[0] if row else None

    cur.execute("""
        SELECT s.name
        FROM msod5.user_skills us
        JOIN msod5.skills s ON s.id = us.skill_id
        WHERE us.user_id = %s
    """, (user_id,))
    
    user_skills = {row[0] for row in cur.fetchall()}
    if not user_skills:
        return []

    cur.execute("""
        SELECT
            v.id,
            v.city_id,
            ARRAY_AGG(s.name) FILTER (WHERE s.name IS NOT NULL)
        FROM msod5.vacancies v
        LEFT JOIN msod5.vacancy_skills vs ON vs.vacancy_id = v.id
        LEFT JOIN msod5.skills s ON s.id = vs.skill_id
        GROUP BY v.id
    """)

    vacancies = cur.fetchall()
    cur.close()
    conn.close()

    scored = []

    for vac_id, city_id, skills in vacancies:
        vacancy_skills = set(skills or [])

        skill_score = jaccard(user_skills, vacancy_skills)
        city_score = 1.0 if city_id == user_city else 0.0

        score = 0.7 * skill_score + 0.3 * city_score
        scored.append((vac_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:limit]

def save_recommendations(user_id: int, recommendations: list):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM msod5.recommendations
        WHERE user_id = %s
    """, (user_id,))

    for vacancy_id, score in recommendations:
        cur.execute("""
            INSERT INTO msod5.recommendations (user_id, vacancy_id, score)
            VALUES (%s, %s, %s)
        """, (user_id, vacancy_id, score))

    conn.commit()
    cur.close()
    conn.close()

def recommend_for_all_users(limit=10):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("SELECT id FROM msod5.users")
    user_ids = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    for user_id in user_ids:
        recs = recommend_vacancies(user_id, limit)
        save_recommendations(user_id, recs)
        print(f"Рекомендации сохранены для user_id={user_id}")

if __name__ == "__main__":
    recommend_for_all_users(limit=10)
    print("Все рекомендации пересчитаны")
