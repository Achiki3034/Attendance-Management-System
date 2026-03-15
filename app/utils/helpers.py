from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def format_datetime(dt):
    if dt is None:
        return 'N/A'
    return dt.strftime('%B %d, %Y %I:%M %p')

def format_date(d):
    if d is None:
        return 'N/A'
    return d.strftime('%B %d, %Y')
