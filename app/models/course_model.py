from app import db
from datetime import datetime

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships with cascade delete
    enrollments = db.relationship(
        'Enrollment',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    sessions = db.relationship(
        'AttendanceSession',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def get_total_sessions(self):
        return self.sessions.count()

    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name}>'