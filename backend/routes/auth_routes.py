from auth.token_utils import get_user_id_from_token, require_user_auth, generate_token
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from db.connection import get_db_connection  # Make sure you have this utility
import mysql.connector

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate and store token
        token = generate_token(user['id'])

        cursor.execute(
            "UPDATE users SET token = %s, is_active = 1 WHERE id = %s",
            (token, user['id'])
        )
        db.commit()

        return jsonify({
            'message': 'Login successful',
            'role': user.get('role', 'user'),
            'token': token
        }), 200

    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # Extract fields
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('fullName')
    age = data.get('age')
    location = data.get('location')
    preferred_lang_obj = data.get('preferredLanguage')

    # Basic validation
    if not all([email, password, full_name, age, location, preferred_lang_obj]):
        return jsonify({'error': 'All fields are required'}), 400

    try:
        age = int(age)
        preferred_language = preferred_lang_obj.get("value")
        if not preferred_language:
            return jsonify({'error': 'Invalid language value'}), 400
    except Exception:
        return jsonify({'error': 'Invalid age or language format'}), 400

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Check if user already exists
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'User already exists'}), 400

        # Hash the password
        hashed_pw = generate_password_hash(password)

        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (email, password, full_name, age, location, preferred_language, active, balance, role)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, 0, 'user')
            """,
            (email, hashed_pw, full_name, age, location, preferred_language)
        )
        db.commit()

        # Get the new user's ID
        user_id = cursor.lastrowid

        # Generate token
        token = generate_token(user_id)

        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'role': 'user'
        }), 201

    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@auth_bp.route('/logout', methods=['POST'])
@require_user_auth  # optional, but recommended to secure logout
def logout():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid token'}), 401

    token = auth_header.split(' ')[1]

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Set is_active = 0 and clear token
        cursor.execute(
            "UPDATE users SET is_active = 0, token = NULL WHERE token = %s",
            (token,)
        )
        db.commit()

        return jsonify({'message': 'Logout successful'}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {err}'}), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@auth_bp.route('/my-courses', methods=['GET'])
@require_user_auth
def get_my_courses():
    user_id = g.user['id']
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT course_id AS id FROM courses_participants WHERE participant_id = %s AND is_active = 1", (user_id,))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(results)
