import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv(dotenv_path='../backend/.env')

def get_db_connection_without_db():
    # Connect without specifying a database, so we can drop the whole DB
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', '')
    )

def drop_database():
    db_name = os.getenv('MYSQL_DATABASE', 'time_to_weave')
    try:
        db = get_db_connection_without_db()
        cursor = db.cursor()
        print(f"Dropping database `{db_name}`...")
        cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        db.commit()
        print(f"Database `{db_name}` dropped successfully.")
        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        print(f"Error dropping database: {err}")

if __name__ == "__main__":
    drop_database()
