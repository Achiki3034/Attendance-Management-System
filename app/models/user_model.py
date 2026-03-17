from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin, lecturer, student
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(300), nullable=True)
    bio = db.Column(db.String(300), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships with cascade delete
    enrollments = db.relationship(
        'Enrollment',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan',
        foreign_keys='Enrollment.student_id'
    )

    attendance_records = db.relationship(
        'AttendanceRecord',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    courses_teaching = db.relationship(
        'Course',
        backref='lecturer',
        lazy='dynamic',
        foreign_keys='Course.lecturer_id'
    )

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'