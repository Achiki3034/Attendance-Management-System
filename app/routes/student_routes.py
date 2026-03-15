from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.services.attendance_service import get_student_attendance_summary
from app.models.attendance_model import AttendanceRecord, AttendanceSession
from app.utils.helpers import role_required
import os

student_bp = Blueprint('student', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    summary = get_student_attendance_summary(current_user.id)
    overall_pct = 0
    total_attended = sum(s['attended'] for s in summary)
    total_missed   = sum(s['missed']   for s in summary)
    if summary:
        valid = [s for s in summary if s['total_sessions'] > 0]
        overall_pct = round(sum(s['percentage'] for s in valid) / len(valid), 1) if valid else 0
    recent_records = AttendanceRecord.query.filter_by(
        student_id=current_user.id).order_by(
        AttendanceRecord.marked_at.desc()).limit(6).all()
    return render_template('student/dashboard.html',
        summary=summary,
        overall_pct=overall_pct,
        total_attended=total_attended,
        total_missed=total_missed,
        recent_records=recent_records)


@student_bp.route('/history')
@login_required
@role_required('student')
def history():
    records = AttendanceRecord.query.filter_by(
        student_id=current_user.id).order_by(
        AttendanceRecord.marked_at.desc()).all()
    summary = get_student_attendance_summary(current_user.id)
    valid = [s for s in summary if s['total_sessions'] > 0]
    overall_pct = round(sum(s['percentage'] for s in valid) / len(valid), 1) if valid else 0
    return render_template('student/history.html', records=records, summary=summary, overall_pct=overall_pct)


@student_bp.route('/profile')
@login_required
@role_required('student')
def profile():
    summary = get_student_attendance_summary(current_user.id)
    total_attended = sum(s['attended'] for s in summary)
    total_sessions = sum(s['total_sessions'] for s in summary)
    overall_pct = 0
    if summary:
        valid = [s for s in summary if s['total_sessions'] > 0]
        overall_pct = round(sum(s['percentage'] for s in valid) / len(valid), 1) if valid else 0
    return render_template('student/profile.html',
        summary=summary,
        total_attended=total_attended,
        total_sessions=total_sessions,
        overall_pct=overall_pct)


@student_bp.route('/profile/update', methods=['POST'])
@login_required
@role_required('student')
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone     = request.form.get('phone', '').strip()
    bio       = request.form.get('bio', '').strip()

    if not full_name:
        flash('Full name cannot be empty.', 'danger')
        return redirect(url_for('student.profile'))

    current_user.full_name = full_name
    current_user.phone     = phone
    current_user.bio       = bio

    # Handle profile picture upload
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"avatar_{current_user.id}.{file.filename.rsplit('.',1)[1].lower()}")
            upload_dir = os.path.join(current_app.root_path, 'static', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            current_user.profile_picture = filename

    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('student.profile'))


@student_bp.route('/profile/change-password', methods=['POST'])
@login_required
@role_required('student')
def change_password():
    current_pw  = request.form.get('current_password', '')
    new_pw      = request.form.get('new_password', '')
    confirm_pw  = request.form.get('confirm_password', '')

    if not check_password_hash(current_user.password_hash, current_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('student.profile'))

    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('student.profile'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('student.profile'))

    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('student.profile'))


@student_bp.route('/course/<int:course_id>')
@login_required
@role_required('student')
def course_detail(course_id):
    from app.models.course_model import Course
    from app.models.enrollment_model import Enrollment
    from app.models.attendance_model import AttendanceSession, AttendanceRecord
    from app.services.attendance_service import calculate_attendance_percentage

    course = Course.query.get_or_404(course_id)
    # ensure student is enrolled
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first_or_404()

    total_sessions = AttendanceSession.query.filter_by(course_id=course_id).count()
    attended_ids = set(
        r.session_id for r in AttendanceRecord.query.filter_by(student_id=current_user.id).all()
    )
    all_sessions = AttendanceSession.query.filter_by(course_id=course_id).order_by(
        AttendanceSession.date.desc()).all()
    attended_sessions = [s for s in all_sessions if s.id in attended_ids]
    missed_sessions   = [s for s in all_sessions if s.id not in attended_ids]
    attended_count = len(attended_sessions)
    missed_count   = len(missed_sessions)
    pct = calculate_attendance_percentage(current_user.id, course_id)

    return render_template('student/course_detail.html',
        course=course,
        all_sessions=all_sessions,
        attended_sessions=attended_sessions,
        missed_sessions=missed_sessions,
        attended_count=attended_count,
        missed_count=missed_count,
        total_sessions=total_sessions,
        pct=pct,
        attended_ids=attended_ids)
