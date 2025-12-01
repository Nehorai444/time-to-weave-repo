import os
import jwt
import datetime
from flask import request, jsonify, g
from functools import wraps
from dotenv import load_dotenv
from db.connection import get_db_connection

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET', 'mysecretkey')  # Fallback for development
JWT_ALGORITHM = 'HS256'


def generate_token(user_id: int) -> str:
    """
    Generates a JWT token with user_id and 7-day expiration.
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    """
    Decodes the token and returns the payload or None if invalid.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_user_id_from_token(req=None):
    """
    Extracts and verifies JWT from the Authorization header, returns user_id.
    """
    if req is None:
        req = request

    auth_header = req.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.replace('Bearer ', '')

    decoded = decode_token(token)
    return decoded.get('user_id') if decoded else None


def verify_token(token: str):
    """
    Verifies token and returns full user object from DB, or None if invalid.
    """
    decoded = decode_token(token)
    if not decoded or 'user_id' not in decoded:
        return None

    user_id = decoded['user_id']
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        return user
    except Exception:
        return None


def require_user_auth(f):
    """
    Flask decorator to protect routes requiring valid user token.
    Attaches user to flask.g.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authorization token missing'}), 401

        user = verify_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401

        g.user = user
        return f(*args, **kwargs)
    return decorated_function
