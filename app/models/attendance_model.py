from app import db
from datetime import datetime
import uuid

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    qr_code_path = db.Column(db.String(300), nullable=True)

    # Relationships
    records = db.relationship('AttendanceRecord', backref='session', lazy='dynamic')
    lecturer = db.relationship('User', foreign_keys=[lecturer_id])

    def close_session(self):
        self.is_active = False
        self.end_time = datetime.utcnow()

    def __repr__(self):
        return f'<Session {self.session_token[:8]}... course={self.course_id}>'

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present')

    __table_args__ = (db.UniqueConstraint('session_id', 'student_id', name='unique_attendance'),)

    def __repr__(self):
        return f'<Record session={self.session_id} student={self.student_id}>'
