from .auth_routes import auth_bp
from .admin_routes import admin_bp
from .course_routes import course_bp
from .feedback_routes import feedback_bp

__all__ = ['auth_bp', 'admin_bp', 'course_bp', 'feedback_bp']
