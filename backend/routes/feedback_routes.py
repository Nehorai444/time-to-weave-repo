from flask import Blueprint, request, jsonify, g
from auth.token_utils import require_user_auth
from datetime import datetime
from db.connection import get_db_connection  # Make sure you have this utility

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

@feedback_bp.route('/submit', methods=['POST'])
@require_user_auth
def submit_feedback():
    user_id = g.user['id']
    data = request.get_json() or {}

    course_id = data.get('courseId')
    session_date = data.get('sessionDate')  # optional
    comment = data.get('comment', '')
    improvement = data.get('improvement', '')
    suggested_topics = data.get('suggestedTopics', '')

    if not course_id:
        return jsonify({'error': 'Missing courseId'}), 400

    # אם יש תאריך, וודא תקינות הפורמט
    if session_date:
        try:
            datetime.strptime(session_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({'error': 'Invalid sessionDate format. Expected YYYY-MM-DD'}), 400

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # אפשרות למנוע כפילויות עבור אותו משתמש, קורס ותאריך
        if session_date:
            cursor.execute("""
                SELECT 1 FROM lesson_feedback
                WHERE participant_id = %s AND course_id = %s AND session_date = %s
            """, (user_id, course_id, session_date))
        else:
            cursor.execute("""
                SELECT 1 FROM lesson_feedback
                WHERE participant_id = %s AND course_id = %s AND session_date IS NULL
            """, (user_id, course_id))

        if cursor.fetchone():
            cursor.close()
            db.close()
            return jsonify({'message': 'Feedback already submitted'}), 200

        cursor.execute("""
            INSERT INTO lesson_feedback (
                participant_id, course_id, session_date,
                comment, improvement_suggestion, suggested_topics
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, course_id, session_date, comment, improvement, suggested_topics))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({'message': 'Feedback submitted successfully'}), 200

    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@feedback_bp.route('/reminder', methods=['GET'])
@require_user_auth
def get_feedback_reminders():
    user_id = g.user['id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM feedback_reminders
            WHERE participant_id = %s AND is_sent = 0
        """, (user_id,))
        reminders = cursor.fetchall()
        cursor.close()
        db.close()

        return jsonify({'reminders': reminders})

    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
