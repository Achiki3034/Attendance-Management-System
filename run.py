from app import create_app, db
from app.models.user_model import User
from app.models.course_model import Course
from app.models.attendance_model import AttendanceSession, AttendanceRecord
from app.models.enrollment_model import Enrollment
from werkzeug.security import generate_password_hash

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Course=Course, Enrollment=Enrollment,
                AttendanceSession=AttendanceSession, AttendanceRecord=AttendanceRecord)

def seed_admin():
    import os
    os.makedirs(os.path.join('app', 'static', 'avatars'), exist_ok=True)
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@university.edu').first():
            admin = User(
                full_name='System Administrator',
                email='admin@university.edu',
                student_id='ADMIN001',
                role='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin account created: admin@university.edu / admin123")

if __name__ == '__main__':
    seed_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)