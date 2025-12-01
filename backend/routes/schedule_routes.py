from flask import Blueprint, jsonify, request, g
from auth.token_utils import require_user_auth
from datetime import datetime, timedelta
from db.connection import get_db_connection

schedule_bp = Blueprint('schedule', __name__, url_prefix='/api/schedule')

@schedule_bp.route('/upcoming', methods=['GET'])
@require_user_auth
def get_upcoming_schedule():
    user_id = g.user['id']
    today = datetime.now().date()
    three_weeks_from_now = today + timedelta(weeks=3)

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT cs.id AS session_id,
                   cs.course_id,
                   c.name AS course_name,
                   cs.session_time,
                   cs.session_date,
                   cs.description,
                   i.full_name AS instructor_name
            FROM courses_participants cp
            JOIN course_sessions cs ON cs.course_id = cp.course_id
            JOIN courses c ON c.id = cp.course_id
            JOIN instructors i ON c.instructor_id = i.id
            WHERE cp.participant_id = %s
              AND cs.session_date BETWEEN %s AND %s
              AND cp.is_active = TRUE
            ORDER BY cs.session_date ASC, cs.session_time ASC
        """

        cursor.execute(query, (user_id, today, three_weeks_from_now))
        sessions = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify(sessions), 200

    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500