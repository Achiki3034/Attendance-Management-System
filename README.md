# CheckinHub — Digital Attendance Management System

A full-featured university attendance system built with Flask.

## Quick Start

### 1. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python run.py
```

The app starts at **http://localhost:5000**

---

## Default Admin Account
| Field    | Value                  |
|----------|------------------------|
| Email    | admin@university.edu   |
| Password | admin123               |

---

## System Roles

| Role      | Capabilities |
|-----------|-------------|
| **Admin**     | Create users, courses, enrollments; view analytics & reports |
| **Lecturer**  | Start sessions, generate QR codes, view attendance lists |
| **Student**   | Scan QR to mark attendance, view personal attendance history |

---

## Workflow

1. **Admin** creates lecturers and students
2. **Admin** creates courses and assigns lecturers
3. **Admin** enrolls students in courses
4. **Lecturer** logs in → selects course → clicks **Start Attendance**
5. A QR code is generated pointing to `/attendance/mark/<session_token>`
6. **Students** scan the QR code (must be logged in and enrolled)
7. Attendance is recorded — duplicate/unauthorized attempts are blocked
8. **Lecturer** closes the session when done
9. Reports and defaulter lists are available to Admin and Lecturer

---

## Project Structure

```
digital_attendance_system/
├── run.py                    # Entry point
├── config.py                 # App configuration
├── requirements.txt
├── app/
│   ├── __init__.py           # App factory
│   ├── models/               # SQLAlchemy models
│   ├── routes/               # Blueprints (auth, admin, lecturer, student)
│   ├── services/             # Business logic
│   ├── utils/                # Helpers & decorators
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS, JS, QR code images
└── database/
    └── attendance.db         # SQLite DB (auto-created)
```

---

## Switching to MySQL

In `config.py`, change `SQLALCHEMY_DATABASE_URI`:
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/attendx_db'
```
Then install: `pip install pymysql`

---

## Security Notes
- Passwords are hashed with `werkzeug.security`
- Role-based access control on every route
- Duplicate attendance prevention via database constraints
- Students cannot mark attendance for courses they're not enrolled in
