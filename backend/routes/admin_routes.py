from flask import Blueprint, request, jsonify, Response
from functools import wraps
from auth.token_utils import get_user_id_from_token, require_user_auth, generate_token
from db.connection import get_db_connection
import mysql.connector
import json
import os
from dotenv import load_dotenv

load_dotenv()  # loads from .env file by default

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# --- Auth decorator for admin ---

def require_admin_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        print('Authorization header:', auth_header)  # DEBUG
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth_header.split(' ')[1]
        if token != ADMIN_TOKEN:
            print('Invalid token:', token)  # DEBUG
            return jsonify({'error': 'Unauthorized'}), 401
        return func(*args, **kwargs)
    return wrapper



@admin_bp.route('/courses/<int:course_id>/participants', methods=['GET'])
@require_admin_auth
def get_course_participants(course_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.full_name, u.email
            FROM users u
            JOIN courses_participants cp ON u.id = cp.participant_id
            WHERE cp.course_id = %s
        """, (course_id,))
        participants = cursor.fetchall()
        return jsonify(participants), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()


# --- Admin Login ---
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        return jsonify({'token': ADMIN_TOKEN}), 200
    else:
        return jsonify({'error': 'Invalid admin credentials'}), 401


@admin_bp.route('/zoom-sessions/<int:course_id>', methods=['POST'])
@require_admin_auth
def add_zoom_session(course_id):
    db = None
    cursor = None
    try:
        data = request.get_json()
        zoom_link = data.get('zoom_link')
        session_datetime = data.get('session_datetime')  # ISO format
        duration_minutes = data.get('duration_minutes')

        if not zoom_link or not session_datetime or not duration_minutes:
            return jsonify({'error': 'Missing required fields'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO zoom_sessions (course_id, zoom_link, session_datetime, duration_minutes)
            VALUES (%s, %s, %s, %s)
        """, (course_id, zoom_link, session_datetime, duration_minutes))
        db.commit()

        return jsonify({'message': 'Zoom session added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()




# --- Get All Courses ---
@admin_bp.route('/courses', methods=['GET'])
@require_admin_auth
def get_courses():
    try:
        db = get_db_connection()
        db.set_charset_collation('utf8mb4')
        cursor = db.cursor(dictionary=True)
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SELECT * FROM courses ORDER BY id")
        courses = cursor.fetchall()

        for course in courses:
            if course.get('schedule'):
                try:
                    course['schedule'] = json.loads(course['schedule'])
                except Exception:
                    pass

        # Manually create response with UTF-8 encoding
        return Response(
            json.dumps(courses, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
    except Exception as e:
        return jsonify({'error': f'Failed to fetch courses: {str(e)}'}), 500
    finally:
        cursor.close()
        db.close()


# --- Admin Dashboard (Static Example) ---
@admin_bp.route('/dashboard', methods=['GET'])
@require_admin_auth
def admin_dashboard():
    data = {
        "activeUsers": 1542,
        "activeCourses": 32,
        "monthlyRevenue": 14800,
        "recentActions": [
            {"id": 1, "text": "New user registered: Sarah Cohen", "timestamp": "5 minutes ago"},
            {"id": 2, "text": "Course \"Knitting Basics\" updated", "timestamp": "20 minutes ago"},
            {"id": 3, "text": "User feedback received", "timestamp": "1 hour ago"},
        ]
    }
    return jsonify(data), 200


# --- Get All Users ---
@admin_bp.route('/users', methods=['GET'])
@require_admin_auth
def get_all_users():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, full_name, email, active, balance
            FROM users
            ORDER BY full_name
        """)
        users = cursor.fetchall()
        return jsonify(users), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# --- Get Courses for a Specific User ---
@admin_bp.route('/users/<int:user_id>/courses', methods=['GET'])
@require_admin_auth
def get_user_courses(user_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT c.id, c.name, IFNULL(cp.paid, FALSE) AS paid
            FROM courses c
            JOIN course_participants cp ON c.id = cp.course_id
            WHERE cp.participant_id = %s
        """
        cursor.execute(query, (user_id,))
        courses = cursor.fetchall()
        return jsonify(courses), 200
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@admin_bp.route('/courses/<int:course_id>/message', methods=['POST'])
@require_admin_auth
def send_course_message(course_id):
    db = None
    cursor = None
    try:
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Insert the message into course_messages table
        cursor.execute("""
            INSERT INTO course_messages (course_id, message)
            VALUES (%s, %s)
        """, (course_id, message))
        db.commit()

        # Fetch email addresses of course participants
        cursor.execute("""
            SELECT u.email
            FROM courses_participants cp
            JOIN users u ON cp.participant_id = u.id
            WHERE cp.course_id = %s
        """, (course_id,))
        recipients = cursor.fetchall()

        # Log recipients
        print(f"[INFO] Message stored for course {course_id}: {message}")
        for recipient in recipients:
            print(f"  - Email: {recipient['email']}")

        return jsonify({
            'message': f'Message stored and sent to {len(recipients)} participants'
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to send course message: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
