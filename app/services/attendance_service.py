from app import db
from app.models.attendance_model import AttendanceSession, AttendanceRecord
from app.models.enrollment_model import Enrollment
from app.models.course_model import Course
from app.models.user_model import User
from datetime import datetime

def calculate_attendance_percentage(student_id, course_id):
    """Calculate attendance percentage for a student in a course."""
    total_sessions = AttendanceSession.query.filter_by(course_id=course_id).count()
    if total_sessions == 0:
        return 0.0
    attended = AttendanceRecord.query.join(AttendanceSession).filter(
        AttendanceRecord.student_id == student_id,
        AttendanceSession.course_id == course_id
    ).count()
    return round((attended / total_sessions) * 100, 1)

def get_student_attendance_summary(student_id):
    """Get full attendance summary for a student across all courses."""
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    summary = []
    for enrollment in enrollments:
        course = enrollment.course
        pct = calculate_attendance_percentage(student_id, course.id)
        total = AttendanceSession.query.filter_by(course_id=course.id).count()
        attended = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceRecord.student_id == student_id,
            AttendanceSession.course_id == course.id
        ).count()
        missed = total - attended
        sessions_list = AttendanceSession.query.filter_by(course_id=course.id).order_by(AttendanceSession.date.desc()).all()
        attended_ids = set(
            r.session_id for r in AttendanceRecord.query.filter_by(student_id=student_id).all()
        )
        missed_sessions = [s for s in sessions_list if s.id not in attended_ids]
        summary.append({
            'course': course,
            'total_sessions': total,
            'attended': attended,
            'missed': missed,
            'missed_sessions': missed_sessions,
            'percentage': pct,
            'low_attendance': pct < 75 and total > 0
        })
    return summary

def get_course_attendance_report(course_id):
    """Get full attendance report for a course."""
    course = Course.query.get(course_id)
    sessions = AttendanceSession.query.filter_by(course_id=course_id).order_by(AttendanceSession.date).all()
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    report = []
    for enrollment in enrollments:
        student = enrollment.student
        pct = calculate_attendance_percentage(student.id, course_id)
        attended = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceSession.course_id == course_id
        ).count()
        report.append({
            'student': student,
            'attended': attended,
            'total': len(sessions),
            'percentage': pct,
            'defaulter': pct < 75
        })
    return course, sessions, report

def get_defaulters():
    """Get all students with attendance below 75% in any course."""
    defaulters = []
    enrollments = Enrollment.query.all()
    seen = set()
    for enrollment in enrollments:
        key = (enrollment.student_id, enrollment.course_id)
        if key in seen:
            continue
        seen.add(key)
        pct = calculate_attendance_percentage(enrollment.student_id, enrollment.course_id)
        total = AttendanceSession.query.filter_by(course_id=enrollment.course_id).count()
        if pct < 75 and total > 0:
            defaulters.append({
                'student': enrollment.student,
                'course': enrollment.course,
                'percentage': pct
            })
    return defaulters
