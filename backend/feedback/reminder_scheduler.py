from datetime import datetime
from db.connection import get_db_connection  # adjust to your connection method

def schedule_feedback_reminders():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    now = datetime.now()
    today = now.date()
    current_time = now.time()

    # Handle lesson-level feedback (after the Zoom session)
    cursor.execute("""
        SELECT cs.course_id, cs.session_date, cs.session_time, cp.participant_id
        FROM course_sessions cs
        JOIN courses_participants cp ON cs.course_id = cp.course_id
        WHERE cs.session_date = %s AND cs.session_time <= %s AND cp.is_active = 1
    """, (today, current_time))

    for session in cursor.fetchall():
        cursor.execute("""
            SELECT 1 FROM feedback_reminders
            WHERE participant_id = %s AND course_id = %s AND session_date = %s AND type = 'lesson'
        """, (session['participant_id'], session['course_id'], session['session_date']))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO feedback_reminders (participant_id, course_id, session_date, type)
                VALUES (%s, %s, %s, 'lesson')
            """, (session['participant_id'], session['course_id'], session['session_date']))

    # Handle course-level feedback (after course is completed)
    cursor.execute("""
        SELECT cp.participant_id, cp.course_id
        FROM courses_participants cp
        WHERE cp.is_active = 0
    """)
    for row in cursor.fetchall():
        cursor.execute("""
            SELECT 1 FROM feedback_reminders
            WHERE participant_id = %s AND course_id = %s AND type = 'course'
        """, (row['participant_id'], row['course_id']))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO feedback_reminders (participant_id, course_id, type)
                VALUES (%s, %s, 'course')
            """, (row['participant_id'], row['course_id']))

    db.commit()
    cursor.close()
    db.close()
