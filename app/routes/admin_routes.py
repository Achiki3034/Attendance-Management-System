from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
import os
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models.user_model import User
from app.models.course_model import Course
from app.models.enrollment_model import Enrollment
from app.models.attendance_model import AttendanceSession, AttendanceRecord
from app.services.attendance_service import get_defaulters
from app.utils.helpers import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_lecturers = User.query.filter_by(role='lecturer').count()
    total_courses = Course.query.count()
    total_sessions = AttendanceSession.query.count()
    recent_sessions = AttendanceSession.query.order_by(AttendanceSession.start_time.desc()).limit(5).all()
    defaulters = get_defaulters()
    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_lecturers=total_lecturers,
        total_courses=total_courses,
        total_sessions=total_sessions,
        recent_sessions=recent_sessions,
        defaulter_count=len(defaulters))

# ── USERS ──────────────────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    students = User.query.filter_by(role='student').all()
    lecturers = User.query.filter_by(role='lecturer').all()
    return render_template('admin/users.html', students=students, lecturers=lecturers)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        student_id = request.form.get('student_id', '').strip()
        role = request.form.get('role', 'student')
        password = request.form.get('password', 'Password@123')
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('admin/create_user.html')
        user = User(
            full_name=full_name,
            email=email,
            student_id=student_id or None,
            role=role,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash(f'{role.capitalize()} account created successfully.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/create_user.html')

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin.users'))

# ── COURSES ────────────────────────────────────────────────────────────────────
@admin_bp.route('/courses')
@login_required
@role_required('admin')
def courses():
    all_courses = Course.query.all()
    return render_template('admin/courses.html', courses=all_courses)

@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_course():
    lecturers = User.query.filter_by(role='lecturer').all()
    if request.method == 'POST':
        course_code = request.form.get('course_code', '').strip().upper()
        course_name = request.form.get('course_name', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        lecturer_id = request.form.get('lecturer_id') or None
        if Course.query.filter_by(course_code=course_code).first():
            flash('Course code already exists.', 'danger')
            return render_template('admin/create_course.html', lecturers=lecturers)
        course = Course(course_code=course_code, course_name=course_name,
                        department=department, semester=semester, lecturer_id=lecturer_id)
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully.', 'success')
        return redirect(url_for('admin.courses'))
    return render_template('admin/create_course.html', lecturers=lecturers)

@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'success')
    return redirect(url_for('admin.courses'))

# ── ENROLLMENTS ────────────────────────────────────────────────────────────────
@admin_bp.route('/enrollments')
@login_required
@role_required('admin')
def enrollments():
    students = User.query.filter_by(role='student').all()
    courses = Course.query.all()
    all_enrollments = Enrollment.query.all()
    return render_template('admin/enrollments.html',
        students=students, courses=courses, enrollments=all_enrollments)

@admin_bp.route('/enrollments/create', methods=['POST'])
@login_required
@role_required('admin')
def create_enrollment():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    if Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
        flash('Student already enrolled in this course.', 'warning')
    else:
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash('Student enrolled successfully.', 'success')
    return redirect(url_for('admin.enrollments'))

@admin_bp.route('/enrollments/delete/<int:enrollment_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash('Enrollment removed.', 'success')
    return redirect(url_for('admin.enrollments'))

# ── REPORTS ────────────────────────────────────────────────────────────────────
@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    defaulters = get_defaulters()
    courses = Course.query.all()
    return render_template('admin/reports.html', defaulters=defaulters, courses=courses)

@admin_bp.route('/reports/course/<int:course_id>')
@login_required
@role_required('admin')
def course_report(course_id):
    from app.services.attendance_service import get_course_attendance_report
    course, sessions, report = get_course_attendance_report(course_id)
    return render_template('admin/course_report.html', course=course, sessions=sessions, report=report)

# ── ADMIN PROFILE ──────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/profile')
@login_required
@role_required('admin')
def profile():
    total_students  = User.query.filter_by(role='student').count()
    total_lecturers = User.query.filter_by(role='lecturer').count()
    total_courses   = Course.query.count()
    total_sessions  = AttendanceSession.query.count()
    return render_template('admin/profile.html',
        total_students=total_students,
        total_lecturers=total_lecturers,
        total_courses=total_courses,
        total_sessions=total_sessions)

@admin_bp.route('/profile/update', methods=['POST'])
@login_required
@role_required('admin')
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone     = request.form.get('phone', '').strip()
    bio       = request.form.get('bio', '').strip()
    if not full_name:
        flash('Full name cannot be empty.', 'danger')
        return redirect(url_for('admin.profile'))
    current_user.full_name = full_name
    current_user.phone     = phone
    current_user.bio       = bio
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
    return redirect(url_for('admin.profile'))

@admin_bp.route('/profile/change-password', methods=['POST'])
@login_required
@role_required('admin')
def change_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    current_pw = request.form.get('current_password', '')
    new_pw     = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')
    if not check_password_hash(current_user.password_hash, current_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('admin.profile'))
    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin.profile'))
    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('admin.profile'))
    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('admin.profile'))