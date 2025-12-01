# import_courses_from_json.py
import json
import mysql.connector
from dotenv import load_dotenv
import os
from faker import Faker
import random
from werkzeug.security import generate_password_hash
import string

load_dotenv(dotenv_path='../backend/.env')

fake = Faker()


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'time_to_weave')
    )

def import_courses():
    with open('../frontend/public/data/he/courses_he.json', encoding='utf-8') as f:
        courses = json.load(f)

    db = get_db_connection()
    cursor = db.cursor()

    for course in courses:
       cursor.execute(
            "INSERT INTO courses (name, category, suitableFor, medicalNote, schedule) VALUES (%s, %s, %s, %s, %s)",
            (course['name'], course['category'], course['suitableFor'], course['medicalNote'], json.dumps(course['schedule']))
        )



    db.commit()
    cursor.close()
    db.close()
    print("✅ Courses imported successfully.")


def add_participant_to_course(course_id: int, participant_id: int, paid: bool = False):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO courses_participants (course_id, participant_id, paid) VALUES (%s, %s, %s)",
            (course_id, participant_id, paid)
        )
        db.commit()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        # טיפול בשגיאות
    finally:
        cursor.close()
        db.close()

def random_password(length=10):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

# def insert_random_users(n=10):
#     db = get_db_connection()
#     cursor = db.cursor()

#     for _ in range(n):
#         email = fake.unique.email()
#         full_name = fake.name()
#         age = random.randint(18, 80)
#         location = fake.city()
#         preferred_language = random.choice(['en', 'he', 'es'])
#         password = generate_password_hash(random_password())
#         balance = random.randint(0, 500)
#         role = random.choices(['user', 'admin'], weights=[0.9, 0.1])[0]
#         active = True
#         is_active = 0
#         token = None

#         try:
#             cursor.execute(
#                 """
#                 INSERT INTO users (
#                     email, password, full_name, age, location,
#                     preferred_language, balance, role,
#                     active, is_active, token
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 """,
#                 (
#                     email, password, full_name, age, location,
#                     preferred_language, balance, role,
#                     active, is_active, token
#                 )
#             )
#             print(f"Inserted user: {full_name} ({email})")
#         except mysql.connector.Error as err:
#             print(f"Error inserting user {email}: {err}")

#     db.commit()
#     cursor.close()
#     db.close()


if __name__ == '__main__':
    import_courses()
    add_participant_to_course(1, 42, True)
    # insert_random_users(10)
