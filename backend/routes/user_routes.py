from flask import Blueprint, jsonify, request, g
from db.connection import get_db_connection
from auth.token_utils import decode_token, require_user_auth

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/user')

@user_bp.route('/available-courses', methods=['GET'])
@require_user_auth
def get_available_courses():
    user_id = g.user["id"]
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch only courses that the user liked and are still marked as liked = TRUE
    cursor.execute("""
        SELECT c.id, c.name, c.category
        FROM courses c
        JOIN course_likes cl ON c.id = cl.course_id
        WHERE cl.user_id = %s AND cl.liked = TRUE
    """, (user_id,))
    
    liked_courses = cursor.fetchall()

    # Mark all as liked = true
    for course in liked_courses:
        course['liked'] = True

    return jsonify({'availableCourses': liked_courses})



@user_bp.route('/schedule', methods=['GET'])
@require_user_auth
def get_user_schedule():
    user_id = g.user.get('id')  # Provided by @require_user_auth

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.schedule
            FROM courses_participants cp
            JOIN courses c ON cp.course_id = c.id
            WHERE cp.participant_id = %s AND cp.is_active = TRUE
        """, (user_id,))

        results = cursor.fetchall()
        all_schedule = []

        for row in results:
            schedule_data = row.get('schedule')
            if not schedule_data:
                continue

            try:
                # Try parsing JSON format (e.g. '["2025-08-01T10:00", "2025-08-03T13:30"]')
                import json
                parsed = json.loads(schedule_data)
                if isinstance(parsed, list):
                    all_schedule.extend(parsed)
                else:
                    all_schedule.append(str(parsed))
            except Exception:
                # Fallback: comma-separated format
                all_schedule.extend([s.strip() for s in schedule_data.split(',')])

        return jsonify({'schedule': all_schedule})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        db.close()



@user_bp.route('/profile', methods=['GET'])
@require_user_auth
def get_user_profile():
    user_id = g.user['id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch user info
        cursor.execute("""
            SELECT full_name AS name,
                age,
                location,
                preferred_language,
                role = 'admin' AS is_manager
            FROM users
            WHERE id = %s AND active = TRUE
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found or inactive'}), 404

        # Fetch courses where user participates
        cursor.execute("""
                SELECT
                    c.id,
                    c.name AS title,
                    c.category,
                    c.suitableFor,
                    c.medicalNote,
                    cp.created_at AS joined
                FROM courses c
                JOIN courses_participants cp ON cp.course_id = c.id
                WHERE cp.participant_id = %s AND cp.is_active = TRUE
            """, (user_id,))


        courses = cursor.fetchall()
        user['courses'] = courses if courses else []

        cursor.close()
        db.close()

        return jsonify(user)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500



@user_bp.route('/course/<int:course_id>/comment', methods=['DELETE'])
@require_user_auth
def delete_course_comment(course_id):
    user_id = g.user_id

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Check if user is manager
    cursor.execute("SELECT is_manager FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    is_manager = user['is_manager']

    # Check if course exists and who created it
    cursor.execute("SELECT creator_id FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    course_creator_id = course['creator_id']

    # Check if user has a comment on this course
    cursor.execute("""
        SELECT comment FROM course_participants
        WHERE user_id = %s AND course_id = %s
    """, (user_id, course_id))
    participation = cursor.fetchone()

    if not participation or not participation['comment']:
        return jsonify({'error': 'No comment found'}), 404

    # Permission check: must be manager OR course creator OR owner of comment
    if not (is_manager or user_id == course_creator_id):
        # Not manager or course creator, so user must own the comment (guaranteed by user_id)
        # User owns the comment because we queried by user_id
        # So permission allowed only if comment owner == user (true here)
        # No extra check needed
        pass

    # Delete comment
    cursor.execute("""
        UPDATE course_participants
        SET comment = NULL
        WHERE user_id = %s AND course_id = %s
    """, (user_id, course_id))
    db.commit()

    return jsonify({'message': 'Comment deleted successfully'})


@user_bp.route('/profile', methods=['PUT'])
@require_user_auth
def update_user_profile():
    user_id = g.user_id  # Set by token_required after token verification

    data = request.get_json()
    key = data.get('key')
    value = data.get('value')

    allowed_fields = {'name', 'age', 'location', 'preferred_language', 'bio'}

    if key not in allowed_fields:
        return jsonify({'error': 'Invalid field key'}), 400

    if key == 'age':
        try:
            value = int(value)
            if value < 0 or value > 120:
                return jsonify({'error': 'Invalid age value'}), 400
        except Exception:
            return jsonify({'error': 'Age must be a number'}), 400

    db = get_db_connection()
    cursor = db.cursor()

    sql = f"UPDATE users SET {key} = %s WHERE id = %s"
    cursor.execute(sql, (value, user_id))
    db.commit()

    return jsonify({'message': 'User updated successfully'})



@user_bp.route('/messages', methods=['GET'])
@require_user_auth
def get_user_messages_and_zoom_sessions():
    user_id = g.user['id']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Get active course IDs
    cursor.execute("""
        SELECT course_id
        FROM courses_participants
        WHERE participant_id = %s AND is_active = TRUE
    """, (user_id,))
    courses = cursor.fetchall()
    course_ids = [c['course_id'] for c in courses]

    if not course_ids:
        return jsonify({"messages": [], "zoom_sessions": []}), 200

    format_strings = ','.join(['%s'] * len(course_ids))

    # Fetch messages
    cursor.execute(f"""
        SELECT id, course_id, message, sent_at
        FROM course_messages
        WHERE course_id IN ({format_strings})
        ORDER BY sent_at DESC
    """, tuple(course_ids))
    messages = cursor.fetchall()

    # Fetch zoom sessions
    cursor.execute(f"""
        SELECT id, course_id, session_datetime, zoom_link, duration_minutes
        FROM zoom_sessions
        WHERE course_id IN ({format_strings})
        ORDER BY session_datetime DESC
    """, tuple(course_ids))
    zoom_sessions = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
        "messages": messages,
        "zoom_sessions": zoom_sessions
    }), 200


@user_bp.route('/liked-course-ids', methods=['GET'])
@require_user_auth
def get_liked_course_ids():
    user_id = g.user["id"]
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT course_id 
        FROM course_likes 
        WHERE user_id = %s AND liked = TRUE
    """, (user_id,))

    liked_ids = [row[0] for row in cursor.fetchall()]

    return jsonify({'likedCourseIds': liked_ids}), 200
