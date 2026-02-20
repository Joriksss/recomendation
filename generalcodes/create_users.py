import random
import psycopg2
from db.config import db_config

FIRST_NAMES = [
    "Алексей", "Дмитрий", "Иван", "Андрей", "Максим",
    "Олег", "Кирилл", "Никита", "Сергей", "Владимир",
    "Анна", "Мария", "Екатерина", "Дарья", "Алина",
    "Ольга", "Юлия", "Ксения", "Полина", "Виктория"
]

LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов",
    "Попов", "Соколов", "Лебедев", "Козлов", "Новиков",
    "Морозов", "Волков", "Фёдоров", "Михайлов", "Беляев"
]

LEVELS = ["junior", "middle", "senior", "none"]

def seed_users(count=100):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("SELECT id FROM msod5.cities")
    city_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id, name FROM msod5.skills")
    skills = cur.fetchall()
    users_created = 0

    for _ in range(count):

        first_name = random.choice(FIRST_NAMES)
        last_name  = random.choice(LAST_NAMES)

        city_id = random.choice(city_ids)
        level   = random.choice(LEVELS)

        cur.execute("""
            INSERT INTO msod5.users
            (first_name, last_name, city_id, level)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            first_name,
            last_name,
            city_id,
            level
        ))

        user_id = cur.fetchone()[0]
        num_skills = random.randint(0, min(3, len(skills)))

        if num_skills > 0:
            selected_skills = random.sample(skills, num_skills)

            for skill in selected_skills:
                skill_id = skill[0]

                cur.execute("""
                    INSERT INTO msod5.user_skills (user_id, skill_id)
                    VALUES (%s, %s)
                """, (user_id, skill_id))

        users_created += 1

        conn.commit()
    cur.close()
    conn.close()

    print(f"Создано пользователей: {users_created}")

if __name__ == "__main__":
    seed_users(100)
