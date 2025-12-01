import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")  # Load environment variables from a .env file

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'time_to_weave'),
        auth_plugin='mysql_native_password'  # Optional: depending on your MySQL setup
    )
