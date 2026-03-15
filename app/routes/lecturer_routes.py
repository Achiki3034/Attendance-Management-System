from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.attendance_model import AttendanceSession, AttendanceRecord
from app.models.course_model import Course
from app.models.enrollment_model import Enrollment
from app.services.qr_service import generate_qr_code
from app.services.attendance_service import get_course_attendance_report
from app.utils.helpers import role_required
import socket


lecturer_bp = Blueprint('lecturer', __name__)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


@lecturer_bp.route('/dashboard')
@login_required
@role_required('lecturer')
def dashboard():
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    active_sessions = AttendanceSession.query.filter_by(
        lecturer_id=current_user.id, is_active=True).all()
    recent_sessions = AttendanceSession.query.filter_by(
        lecturer_id=current_user.id).order_by(
        AttendanceSession.start_time.desc()).limit(5).all()
    return render_template('lecturer/dashboard.html',
        courses=courses, active_sessions=active_sessions, recent_sessions=recent_sessions)


@lecturer_bp.route('/courses')
@login_required
@role_required('lecturer')
def courses():
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    return render_template('lecturer/courses.html', courses=courses)


@lecturer_bp.route('/session/start/<int:course_id>', methods=['POST'])
@login_required
@role_required('lecturer')
def start_session(course_id):
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('lecturer.dashboard'))

    existing = AttendanceSession.query.filter_by(
        course_id=course_id, is_active=True).first()
    if existing:
        flash('An active session already exists for this course.', 'warning')
        return redirect(url_for('lecturer.session_detail', session_id=existing.id))

    session = AttendanceSession(course_id=course_id, lecturer_id=current_user.id)
    db.session.add(session)
    db.session.flush()

    base_url = f"http://{get_local_ip()}:5000"
    filename = generate_qr_code(session.session_token, base_url)

    session.qr_code_path = filename
    db.session.commit()

    flash(f'Attendance session started for {course.course_name}.', 'success')
    return redirect(url_for('lecturer.session_detail', session_id=session.id))


@lecturer_bp.route('/session/<int:session_id>')
@login_required
@role_required('lecturer')
def session_detail(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    records = AttendanceRecord.query.filter_by(session_id=session_id).all()
    enrolled_count = Enrollment.query.filter_by(course_id=session.course_id).count()
    return render_template('lecturer/session_detail.html',
        session=session, records=records, enrolled_count=enrolled_count)


@lecturer_bp.route('/session/close/<int:session_id>', methods=['POST'])
@login_required
@role_required('lecturer')
def close_session(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    if session.lecturer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('lecturer.dashboard'))
    session.close_session()
    db.session.commit()
    flash('Session closed successfully.', 'success')
    return redirect(url_for('lecturer.dashboard'))


@lecturer_bp.route('/reports/<int:course_id>')
@login_required
@role_required('lecturer')
def course_report(course_id):
    course, sessions, report = get_course_attendance_report(course_id)
    if course.lecturer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('lecturer.dashboard'))
    return render_template('lecturer/course_report.html',
        course=course, sessions=sessions, report=report)

# ── LECTURER PROFILE ───────────────────────────────────────────────────────────
import os
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

ALLOWED_EXTENSIONS_L = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file_l(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_L

@lecturer_bp.route('/profile')
@login_required
@role_required('lecturer')
def profile():
    from app.models.attendance_model import AttendanceSession, AttendanceRecord
    courses        = Course.query.filter_by(lecturer_id=current_user.id).all()
    total_sessions = AttendanceSession.query.filter_by(lecturer_id=current_user.id).count()
    total_students = sum(
        Enrollment.query.filter_by(course_id=c.id).count() for c in courses
    )
    return render_template('lecturer/profile.html',
        courses=courses,
        total_sessions=total_sessions,
        total_students=total_students)

@lecturer_bp.route('/profile/update', methods=['POST'])
@login_required
@role_required('lecturer')
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone     = request.form.get('phone', '').strip()
    bio       = request.form.get('bio', '').strip()
    if not full_name:
        flash('Full name cannot be empty.', 'danger')
        return redirect(url_for('lecturer.profile'))
    current_user.full_name = full_name
    current_user.phone     = phone
    current_user.bio       = bio
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and file.filename != '' and allowed_file_l(file.filename):
            filename = secure_filename(f"avatar_{current_user.id}.{file.filename.rsplit('.',1)[1].lower()}")
            upload_dir = os.path.join(current_app.root_path, 'static', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            current_user.profile_picture = filename
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('lecturer.profile'))

@lecturer_bp.route('/profile/change-password', methods=['POST'])
@login_required
@role_required('lecturer')
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw     = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')
    if not check_password_hash(current_user.password_hash, current_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('lecturer.profile'))
    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('lecturer.profile'))
    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('lecturer.profile'))
    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('lecturer.profile'))