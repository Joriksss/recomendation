from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from db.config import db_config
from main import main as parse_vacancies
from generalcodes.recomendation import (
    recommend_vacancies,
    save_recommendations
)

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(**db_config)

@app.route("/")
def index():
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
    SELECT
        v.title,
        c.name AS city,
        v.experience,
        v.salary,
        v.url
    FROM msod5.vacancies v
    JOIN msod5.cities c ON c.id = v.city_id
    LIMIT 5
    """)

    vacancies = [
        {
            "title": r[0],
            "city": r[1],
            "experience": r[2],
            "salary": r[3],
            "url": r[4]
        }
        for r in cur.fetchall()
    ]

    cur.execute("""
    SELECT
        v.title,
        c.name AS city,
        v.experience,
        v.salary,
        v.url
    FROM msod5.vacancies v
    JOIN msod5.cities c ON c.id = v.city_id
    ORDER BY RANDOM()
    LIMIT 6
    """)

    day_vacancies = [
        {
            "title": r[0],
            "city": r[1],
            "experience": r[2],
            "salary": r[3],
            "url": r[4]
        }
        for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        vacancies=vacancies,
        day_vacancies=day_vacancies
    )


@app.route("/run_recommendations/<int:user_id>", methods=["POST"])
def run_recommendations(user_id):

    recs = recommend_vacancies(user_id, limit=10)
    save_recommendations(user_id, recs)

    return redirect(url_for("user_profile", user_id=user_id))


# Профиля юзеров
@app.route("/user/<int:user_id>")
def user_profile(user_id):

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            u.id,
            u.first_name,
            u.last_name,
            u.level,
            c.name
        FROM msod5.users u
        LEFT JOIN msod5.cities c ON c.id = u.city_id
        WHERE u.id = %s
    """, (user_id,))
    row = cur.fetchone()

    if row is None:
        return "User not found", 404

    user = {
        "id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "level": row[3],
        "city": row[4],
    }

    cur.execute("""
        SELECT s.name
        FROM msod5.user_skills us
        JOIN msod5.skills s ON s.id = us.skill_id
        WHERE us.user_id = %s
    """, (user_id,))
    skills = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT 
            v.title,
            c.name,
            v.experience,
            v.salary,
            v.url
        FROM msod5.recommendations r
        JOIN msod5.vacancies v ON v.id = r.vacancy_id
        LEFT JOIN msod5.cities c ON c.id = v.city_id
        WHERE r.user_id = %s
        ORDER BY r.score DESC
    """, (user_id,))
    recs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "user_profile.html",
        user=user,
        skills=skills,
        recs=recs
    )


@app.route("/recommendations")
def user_recommendations():
    user_id = request.args.get("user_id")

    if not user_id:
        return "User ID не указан", 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM msod5.users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                return "Пользователь не найден", 404
            user_name = user[0]

            cur.execute("""
                SELECT v.title, comp.name AS company, c.name AS city, r.score, v.url
                FROM msod5.recommendations r
                JOIN msod5.vacancies v ON v.id = r.vacancy_id
                LEFT JOIN msod5.companies comp ON comp.id = v.company_id
                LEFT JOIN msod5.cities c ON c.id = v.city_id
                WHERE r.user_id = %s
                ORDER BY r.score DESC
                LIMIT 5
            """, (user_id,))
            recommendations = cur.fetchall()

    recs = []
    for title, company, city, score, url in recommendations:
        recs.append({
            "title": title,
            "company": company,
            "city": city,
            "score": score,
            "url": url
        })

    return render_template("Recommendation.html", user_id=user_id, user_name=user_name, recommendations=recs)

@app.route("/all_vacancies")
def all_vacancies():
    return render_template("all_vacancies.html")

@app.route("/users")
def users_page():
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            u.id,
            u.first_name,
            u.last_name,
            c.name AS city,
            u.level
        FROM msod5.users u
        LEFT JOIN msod5.cities c ON c.id = u.city_id
        ORDER BY u.id
    """)
    users = [
        {
            "id": r[0],
            "first_name": r[1],
            "last_name": r[2],
            "city": r[3],
            "level": r[4]
        }
        for r in cur.fetchall()
    ]

    cur.execute("""
        SELECT id, name
        FROM msod5.cities
        ORDER BY name
    """)
    cities = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

    cur.execute("""
        SELECT id, name
        FROM msod5.skills
        ORDER BY name
    """)
    skills = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template(
        "users.html",
        users=users,
        cities=cities,
        skills=skills
    )


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM msod5.users WHERE id = %s",
        (user_id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("users_page"))


@app.route("/add_user", methods=["POST"])
def add_user():
    first_name = request.form["first_name"]
    last_name  = request.form["last_name"]
    city_id    = request.form["city_id"]
    level      = request.form["level"]

    skills = request.form.getlist("skills")

    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO msod5.users
        (first_name, last_name, city_id, level)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (first_name, last_name, city_id, level))

    user_id = cur.fetchone()[0]

    for skill_id in skills:
        cur.execute("""
            INSERT INTO msod5.user_skills
            (user_id, skill_id)
            VALUES (%s, %s)
        """, (user_id, skill_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/users")


# @app.route("/refresh")
# def refresh():
#     parse_vacancies()
#     recommend_for_all_users()
#     return redirect(url_for("users_page"))


if __name__ == "__main__":
    app.run(debug=True)
