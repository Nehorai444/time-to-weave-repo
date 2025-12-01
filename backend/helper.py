import jwt
from flask import request
from your_app.config import SECRET_KEY  # Replace with your actual key

def get_user_id_from_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get('id')
    except jwt.InvalidTokenError:
        return None

