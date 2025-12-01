import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='../backend/.env')

# הגדרות חיבור
config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
}

DB_NAME = os.getenv('MYSQL_DATABASE', 'time_to_weave')

TABLES = {
    'users': (
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            age INT NOT NULL,
            location VARCHAR(255) NOT NULL,
            preferred_language VARCHAR(10) NOT NULL,
            balance INT DEFAULT 0,

            role ENUM('user', 'admin') DEFAULT 'user',

            active BOOLEAN DEFAULT TRUE,        -- Whether account is enabled
            is_active TINYINT(1) DEFAULT 0,     -- Whether user is currently logged in
            token TEXT,                         -- Active session token (JWT)

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """
    ),
    "courses": (
        """
        CREATE TABLE courses (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(255),
            suitableFor VARCHAR(255),
            medicalNote TEXT,
            schedule JSON
        );

        """
    ),
    "course_likes": (
        """
         CREATE TABLE course_likes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            course_id INT NOT NULL,
            liked BOOLEAN NOT NULL DEFAULT TRUE,
            liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );
        """
    ),
    "courses_participants":(
        """
        CREATE TABLE courses_participants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            participant_id INT NOT NULL,
            paid BOOLEAN NOT NULL DEFAULT FALSE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            CONSTRAINT fk_participant FOREIGN KEY (participant_id) REFERENCES users(id) ON DELETE CASCADE,

            UNIQUE KEY uq_course_participant (course_id, participant_id)
        );

        """
    ),
    "trial_participants": (
        """
        CREATE TABLE trial_participants (
            id INT PRIMARY KEY AUTO_INCREMENT,
            course_id INT NOT NULL,
            participant_id INT NOT NULL,
            trial_date DATETIME NOT NULL,
            attended BOOLEAN DEFAULT FALSE,  -- האם הגיע לשיעור הניסיון
            feedback TEXT,                   -- אפשרות למשוב מהמשתמש או מהמרצה
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (participant_id) REFERENCES users(id)
        );
        """
    ),
    "lesson_feedback": (
        """
       CREATE TABLE IF NOT EXISTS lesson_feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            participant_id INT NOT NULL,
            course_id INT NOT NULL,
            session_date DATE NOT NULL,
            comment TEXT,
            improvement_suggestion TEXT,
            suggested_topics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (participant_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );
        """
    ),

    "course_sessions": (
    """
    CREATE TABLE course_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        course_id INT NOT NULL,
        session_date DATE NOT NULL,
        session_time TIME NOT NULL,
        description VARCHAR(255) DEFAULT NULL,
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );

    """
    ),
    "feedback_reminders": (
    """
    CREATE TABLE feedback_reminders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        participant_id INT NOT NULL,
        course_id INT NOT NULL,
        session_date DATE,
        type ENUM('lesson', 'course') NOT NULL,
        is_sent BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (participant_id) REFERENCES users(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );
    """
    ),
    "payments":(
        """
        CREATE TABLE payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            payment_method VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        """
    ),"course_participation": (
        """ 
         CREATE TABLE course_participation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            course_id INT NOT NULL,
            hours FLOAT NOT NULL,
            participated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );

        """
    ), "zoom_sessions": (
        """
        CREATE TABLE zoom_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            session_datetime DATETIME NOT NULL,
            zoom_link TEXT,
            duration_minutes INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );
        """
    ), "course_messages": (
        """
        CREATE TABLE course_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            message TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        """
    )
    

    
   
    
}





def create_database(cursor):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"✅ Database '{DB_NAME}' created or already exists.")
    except mysql.connector.Error as err:
        print(f"❌ Failed to create database: {err}")
        exit(1)


def create_tables(cursor):
    for table_name, ddl in TABLES.items():
        try:
            print(f"🔧 Creating table '{table_name}'...")
            cursor.execute(ddl)
            print(f"✅ Table '{table_name}' ready.")
        except mysql.connector.Error as err:
            print(f"❌ Failed to create table {table_name}: {err}")


def main():
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        create_database(cursor)

        connection.database = DB_NAME

        create_tables(cursor)

        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        print(f"❌ Connection error: {err}")


if __name__ == '__main__':
    main()
