from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user_model import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for(f'{user.role}.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        if student_id and User.query.filter_by(student_id=student_id).first():
            flash('Student ID already in use.', 'danger')
            return render_template('register.html')
        user = User(
            full_name=full_name,
            email=email,
            student_id=student_id or None,
            password_hash=generate_password_hash(password),
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/attendance/mark/<session_token>')
@login_required
def mark_attendance(session_token):
    from app.models.attendance_model import AttendanceSession, AttendanceRecord
    from app.models.enrollment_model import Enrollment
    session = AttendanceSession.query.filter_by(session_token=session_token).first_or_404()
    if not session.is_active:
        flash('This attendance session has ended.', 'warning')
        return redirect(url_for('student.dashboard'))
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, course_id=session.course_id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('student.dashboard'))
    existing = AttendanceRecord.query.filter_by(
        session_id=session.id, student_id=current_user.id).first()
    if existing:
        flash('Attendance already marked for this session.', 'info')
        return redirect(url_for('student.dashboard'))
    record = AttendanceRecord(session_id=session.id, student_id=current_user.id)
    db.session.add(record)
    db.session.commit()
    flash(f'✓ Attendance marked for {session.course.course_name}!', 'success')
    return redirect(url_for('student.dashboard'))
