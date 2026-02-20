import psycopg2

conn = psycopg2.connect(
    host="89.223.65.229",
    port=5432,
    database="msod_database",
    user="big_data_engineer",
    password="H4d00p_Spark$"
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS msod5.cities (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS msod5.companies (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS msod5.skills (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS msod5.users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city_id INT REFERENCES msod5.cities(id),
    level TEXT CHECK (level IN ('junior', 'middle', 'senior', 'none')) DEFAULT 'none'
);

CREATE TABLE IF NOT EXISTS msod5.user_skills (
    user_id INT REFERENCES msod5.users(id) ON DELETE CASCADE,
    skill_id INT REFERENCES msod5.skills(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, skill_id)
);

CREATE TABLE IF NOT EXISTS msod5.vacancies (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    city_id INT REFERENCES msod5.cities(id),
    company_id INT REFERENCES msod5.companies(id),
    experience TEXT,
    category TEXT CHECK (category IN ('professional', 'general')),
    url TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS msod5.vacancy_skills (
    vacancy_id INT REFERENCES msod5.vacancies(id) ON DELETE CASCADE,
    skill_id INT REFERENCES msod5.skills(id) ON DELETE CASCADE,
    PRIMARY KEY (vacancy_id, skill_id)
);

CREATE TABLE IF NOT EXISTS msod5.recommendations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES msod5.users(id),
    vacancy_id INT REFERENCES msod5.vacancies(id),
    score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""
)

conn.commit()
cursor.close()
conn.close()

print("Таблица создана")