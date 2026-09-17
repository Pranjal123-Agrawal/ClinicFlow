from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = "clinicflow-development-secret"

DATABASE = "clinic.db"


def create_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT
        )
    """)

    # Patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            email TEXT UNIQUE,
            phone TEXT
        )
    """)

    # Appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    # Add start_at and end_at columns for STEP 13
    cursor.execute("PRAGMA table_info(appointments)")
    appointment_columns = [
        column[1] for column in cursor.fetchall()
    ]

    if "start_at" not in appointment_columns:
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN start_at TEXT
        """)

    if "end_at" not in appointment_columns:
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN end_at TEXT
        """)

    # Add sample doctors only if table is empty
    cursor.execute("SELECT COUNT(*) FROM doctors")
    doctor_count = cursor.fetchone()[0]

    if doctor_count == 0:
        doctors = [
            (
                "Dr. Aisha Sharma",
                "General Medicine",
                "aisha@clinic.com",
                "9876543210"
            ),
            (
                "Dr. Rahul Mehta",
                "Dermatology",
                "rahul@clinic.com",
                "9876543211"
            ),
            (
                "Dr. Neha Kapoor",
                "Pediatrics",
                "neha@clinic.com",
                "9876543212"
            )
        ]

        cursor.executemany("""
            INSERT INTO doctors
            (name, specialization, email, phone)
            VALUES (?, ?, ?, ?)
        """, doctors)

    conn.commit()
    conn.close()

    print("Database created successfully!")


@app.route("/")
def home():
    return "ClinicFlow is running!"


# STEP 8 - Registration
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()

        return jsonify({
            "error": "Email already registered"
        }), 409

    password_hash = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        email,
        password_hash,
        "staff"
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Registration successful"
    }), 201


# STEP 9 - Login
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, password, role
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    user_id, name, user_email, password_hash, role = user

    if not check_password_hash(password_hash, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    session["user_id"] = user_id
    session["user_name"] = name
    session["user_role"] = role

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user_id,
            "name": name,
            "email": user_email,
            "role": role
        }
    }), 200


# STEP 11 - Doctor API
@app.route("/api/doctors", methods=["GET"])
def get_doctors():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, specialization
        FROM doctors
        ORDER BY name
    """)

    doctors = cursor.fetchall()
    conn.close()

    doctor_list = []

    for doctor in doctors:
        doctor_list.append({
            "id": doctor[0],
            "name": doctor[1],
            "specialty": doctor[2]
        })

    return jsonify(doctor_list), 200


# STEP 12 - Patient API
@app.route("/api/patients", methods=["GET"])
def get_patients():

    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    sort = request.args.get("sort", "name")
    order = request.args.get("order", "asc").lower()

    if page < 1:
        page = 1

    if limit < 1:
        limit = 10

    allowed_sort_columns = {
        "name": "name",
        "age": "age",
        "gender": "gender",
        "email": "email",
        "phone": "phone"
    }

    sort_column = allowed_sort_columns.get(sort, "name")
    sort_order = "DESC" if order == "desc" else "ASC"

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    search_condition = ""
    search_value = f"%{q}%"

    if q:
        search_condition = """
            WHERE name LIKE ?
               OR email LIKE ?
               OR phone LIKE ?
        """

    if q:
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM patients
            {search_condition}
            """,
            (
                search_value,
                search_value,
                search_value
            )
        )
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM patients
        """)

    total = cursor.fetchone()[0]

    offset = (page - 1) * limit

    query = f"""
        SELECT id, name, age, gender, email, phone
        FROM patients
        {search_condition}
        ORDER BY {sort_column} {sort_order}
        LIMIT ? OFFSET ?
    """

    if q:
        cursor.execute(
            query,
            (
                search_value,
                search_value,
                search_value,
                limit,
                offset
            )
        )
    else:
        cursor.execute(
            query,
            (
                limit,
                offset
            )
        )

    patients = cursor.fetchall()
    conn.close()

    patient_list = []

    for patient in patients:
        patient_list.append({
            "id": patient[0],
            "name": patient[1],
            "age": patient[2],
            "gender": patient[3],
            "email": patient[4],
            "phone": patient[5]
        })

    total_pages = (total + limit - 1) // limit

    return jsonify({
        "patients": patient_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    }), 200


# STEP 13 - Appointment Booking
@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    doctor_id = data.get("doctor_id")
    patient_name = data.get("patient_name")
    patient_phone = data.get("patient_phone")
    patient_email = data.get("patient_email")
    start_at = data.get("start_at")
    end_at = data.get("end_at")

    # Required fields
    if not doctor_id or not patient_name or not patient_phone:
        return jsonify({
            "error": "doctor_id, patient_name and patient_phone are required"
        }), 400

    if not start_at or not end_at:
        return jsonify({
            "error": "start_at and end_at are required"
        }), 400

    # Validate date/time
    try:
        start_datetime = datetime.fromisoformat(start_at)
        end_datetime = datetime.fromisoformat(end_at)
    except ValueError:
        return jsonify({
            "error": "Invalid date/time format. Use YYYY-MM-DDTHH:MM"
        }), 400

    # End must be after start
    if end_datetime <= start_datetime:
        return jsonify({
            "error": "end_at must be after start_at"
        }), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check doctor
    cursor.execute("""
        SELECT id, name, specialization
        FROM doctors
        WHERE id = ?
    """, (doctor_id,))

    doctor = cursor.fetchone()

    if not doctor:
        conn.close()

        return jsonify({
            "error": "Doctor not found"
        }), 404

    # Find patient by email
    patient = None

    if patient_email:
        cursor.execute("""
            SELECT id, name, phone, email
            FROM patients
            WHERE email = ?
        """, (patient_email,))

        patient = cursor.fetchone()

    # If not found, find by phone
    if not patient:
        cursor.execute("""
            SELECT id, name, phone, email
            FROM patients
            WHERE phone = ?
        """, (patient_phone,))

        patient = cursor.fetchone()

    # Create patient if not found
    if not patient:
        cursor.execute("""
            INSERT INTO patients
            (name, phone, email)
            VALUES (?, ?, ?)
        """, (
            patient_name,
            patient_phone,
            patient_email
        ))

        patient_id = cursor.lastrowid

    else:
        patient_id = patient[0]

    # Store date/time in existing columns too
    appointment_date = start_datetime.strftime("%Y-%m-%d")
    appointment_time = start_datetime.strftime("%H:%M")

    # Insert appointment
    cursor.execute("""
        INSERT INTO appointments
        (
            doctor_id,
            patient_id,
            appointment_date,
            appointment_time,
            status,
            start_at,
            end_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doctor_id,
        patient_id,
        appointment_date,
        appointment_time,
        "Pending",
        start_at,
        end_at
    ))

    appointment_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Appointment booked successfully",
        "appointment": {
            "id": appointment_id,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "patient_email": patient_email,
            "start_at": start_at,
            "end_at": end_at,
            "status": "Pending"
        }
    }), 201


if __name__ == "__main__":
    create_database()
    app.run(debug=True)