from flask import Blueprint, request, jsonify, g, Response
from auth.token_utils import decode_token, require_user_auth
from db.connection import get_db_connection
import json

course_bp = Blueprint('course', __name__, url_prefix='/api/courses')


@course_bp.route('/my-courses', methods=['GET'])
@require_user_auth
def get_user_courses_with_progress():
    user_id = g.user['id']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT 
            c.id AS course_id,
            c.name,
            c.category,
            c.suitableFor,
            c.medicalNote,
            c.schedule,
            0 AS hours_participated
        FROM courses_participants cp
        JOIN courses c ON cp.course_id = c.id
        WHERE cp.participant_id = %s
        AND cp.is_active = TRUE;
    """
    cursor.execute(query, (user_id,))
    courses = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(courses)





@course_bp.route('/<int:course_id>/register', methods=['POST'])
@require_user_auth
def register_course(course_id):
    """
    Register the authenticated user to the specified course.
    """
    user_id = g.user['id']

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # ✅ Debug print
        print(f"Trying to register user {user_id} to course {course_id}")

        # ✅ Ensure course exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        if not course:
            print(f"Course {course_id} not found in DB.")
            return jsonify({'error': 'Course not found'}), 404

        # ✅ Ensure user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"User {user_id} not found in DB.")
            return jsonify({'error': 'User not found'}), 404

        # ✅ Check if user is already registered to the course
        cursor.execute(
            "SELECT id, is_active FROM courses_participants WHERE course_id = %s AND participant_id = %s",
            (course_id, user_id)
        )
        existing = cursor.fetchone()

        if existing:
            if existing[1]:  # already active
                return jsonify({'message': 'Already registered'}), 200
            else:
                cursor.execute(
                    "UPDATE courses_participants SET is_active = TRUE WHERE id = %s",
                    (existing[0],)
                )
                db.commit()
                return jsonify({'message': 'Re-activated registration'}), 200

        # ✅ New registration
        cursor.execute(
            "INSERT INTO courses_participants (course_id, participant_id, is_active) VALUES (%s, %s, TRUE)",
            (course_id, user_id)
        )
        db.commit()

        return jsonify({'message': 'Registered successfully'}), 200

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    finally:
        cursor.close()
        db.close()


@course_bp.route('/like', methods=['POST'])
@require_user_auth
def like_course():
    """
    Toggle like/unlike for a course by the authenticated user.
    """
    data = request.get_json()
    user_id = g.user['id']
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'error': 'Missing course_id'}), 400

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Check if already liked
        cursor.execute(
            "SELECT 1 FROM course_likes WHERE user_id = %s AND course_id = %s",
            (user_id, course_id)
        )

        if cursor.fetchone():
            cursor.execute(
                "DELETE FROM course_likes WHERE user_id = %s AND course_id = %s",
                (user_id, course_id)
            )
            liked = False
        else:
            cursor.execute(
                "INSERT INTO course_likes (user_id, course_id) VALUES (%s, %s)",
                (user_id, course_id)
            )
            liked = True

        db.commit()
        return jsonify({'liked': liked}), 200

    except Exception as err:
        return jsonify({'error': f'Database error: {err}'}), 500

    finally:
        cursor.close()
        db.close()
