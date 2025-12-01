import os
import jwt
import datetime
import mysql.connector
from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables early
load_dotenv()

# Configuration constants
JWT_SECRET = os.getenv("JWT_SECRET", "mysecretkey")
JWT_ALGORITHM = "HS256"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'time_to_weave')

# Import blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.course_routes import course_bp
from routes.feedback_routes import feedback_bp
from routes.payment_routes import payment_bp
from routes.schedule_routes import schedule_bp
from routes.user_routes import user_bp

# Initialize Flask app with frontend static files
app = Flask(
    __name__,
    static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/dist/spa')),
    static_url_path=''
)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# Enable CORS
CORS(app)

# Database connection helper
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'time_to_weave')
    )

# JWT utilities
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('user_id')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def verify_token(token):
    user_id = decode_token(token)
    if not user_id:
        return None
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user

# Auth decorators
def require_user_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        token = auth_header[len('Bearer '):]

        user_id = decode_token(token)  # your function that extracts user_id from token
        if not user_id:
            return jsonify({'error': 'Invalid token'}), 401

        g.user_id = user_id  # <-- THIS IS CRUCIAL

        return f(*args, **kwargs)
    return decorated

def require_admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token != ADMIN_TOKEN:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(course_bp, url_prefix='/api/courses')
app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
app.register_blueprint(payment_bp, url_prefix='/api/payments')
app.register_blueprint(schedule_bp, url_prefix='/api/schedule')
app.register_blueprint(user_bp, url_prefix='/api/user')

# Background scheduler task example
def schedule_feedback_reminders():
    # Placeholder: implement reminder logic here
    print("⏰ Running feedback reminder task")

scheduler = BackgroundScheduler()
scheduler.add_job(schedule_feedback_reminders, 'interval', minutes=10)
scheduler.start()

# Serve static frontend assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    full_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# Run the app
if __name__ == '__main__':
    app.run(port=3000, debug=True)
