from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.secret_key = "clinicflow-development-secret"

DATABASE = "clinic.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # DOCTORS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT
        )
    """)

    # -----------------------------------------------------
    # PATIENTS TABLE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # APPOINTMENTS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            start_at TEXT,
            end_at TEXT,
            cancellation_fee INTEGER DEFAULT 0,
            cancelled_at TEXT,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    # -----------------------------------------------------
    # ADD NEW COLUMNS TO OLD DATABASE
    # -----------------------------------------------------

    cursor.execute("PRAGMA table_info(appointments)")

    appointment_columns = [
        row["name"] for row in cursor.fetchall()
    ]

    if "start_at" not in appointment_columns:
        cursor.execute(
            "ALTER TABLE appointments ADD COLUMN start_at TEXT"
        )

    if "end_at" not in appointment_columns:
        cursor.execute(
            "ALTER TABLE appointments ADD COLUMN end_at TEXT"
        )

    if "cancellation_fee" not in appointment_columns:
        cursor.execute(
            "ALTER TABLE appointments ADD COLUMN cancellation_fee INTEGER DEFAULT 0"
        )

    if "cancelled_at" not in appointment_columns:
        cursor.execute(
            "ALTER TABLE appointments ADD COLUMN cancelled_at TEXT"
        )

    # -----------------------------------------------------
    # SEED DOCTORS
    # -----------------------------------------------------

    cursor.execute("SELECT COUNT(*) AS count FROM doctors")

    doctor_count = cursor.fetchone()["count"]

    if doctor_count == 0:
        doctors = [
            (
                "Dr. Aisha Sharma",
                "General Medicine",
                "aisha@clinicflow.com",
                "9876543210"
            ),
            (
                "Dr. Rahul Mehta",
                "Dermatology",
                "rahul@clinicflow.com",
                "9876543211"
            ),
            (
                "Dr. Neha Kapoor",
                "Pediatrics",
                "neha@clinicflow.com",
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


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return "ClinicFlow is running!"


# =========================================================
# STEP 8 - USER REGISTRATION
# =========================================================

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
    role = data.get("role", "staff")

    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    conn = get_db_connection()
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

    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users
        (name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, (
        name,
        email,
        hashed_password,
        role
    ))

    conn.commit()

    user_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "role": role
        }
    }), 201


# =========================================================
# STEP 9 - USER LOGIN
# =========================================================

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

    conn = get_db_connection()
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

    if not check_password_hash(user["password"], password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }), 200


# =========================================================
# STEP 11 - GET DOCTORS
# =========================================================

@app.route("/api/doctors", methods=["GET"])
def get_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            specialization
        FROM doctors
        ORDER BY name
    """)

    doctors = cursor.fetchall()

    conn.close()

    result = []

    for doctor in doctors:
        result.append({
            "id": doctor["id"],
            "name": doctor["name"],
            "specialty": doctor["specialization"]
        })

    return jsonify(result), 200


# =========================================================
# STEP 12 - PATIENT SEARCH, PAGINATION AND SORTING
# =========================================================

@app.route("/api/patients", methods=["GET"])
def get_patients():
    q = request.args.get("q", "").strip()

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({
            "error": "page and limit must be integers"
        }), 400

    if page < 1:
        return jsonify({
            "error": "page must be at least 1"
        }), 400

    if limit < 1:
        return jsonify({
            "error": "limit must be at least 1"
        }), 400

    sort = request.args.get("sort", "name")
    order = request.args.get("order", "asc").lower()

    allowed_sort_columns = {
        "name": "name",
        "age": "age",
        "gender": "gender",
        "email": "email",
        "phone": "phone"
    }

    if sort not in allowed_sort_columns:
        return jsonify({
            "error": "Invalid sort field"
        }), 400

    if order not in ["asc", "desc"]:
        return jsonify({
            "error": "order must be asc or desc"
        }), 400

    sort_column = allowed_sort_columns[sort]
    sort_order = order.upper()

    conn = get_db_connection()
    cursor = conn.cursor()

    where_clause = ""
    params = []

    if q:
        where_clause = """
            WHERE
                name LIKE ?
                OR email LIKE ?
                OR phone LIKE ?
        """

        search_value = f"%{q}%"

        params = [
            search_value,
            search_value,
            search_value
        ]

    cursor.execute(
        f"""
        SELECT COUNT(*) AS count
        FROM patients
        {where_clause}
        """,
        params
    )

    total = cursor.fetchone()["count"]

    offset = (page - 1) * limit

    cursor.execute(
        f"""
        SELECT
            id,
            name,
            age,
            gender,
            email,
            phone
        FROM patients
        {where_clause}
        ORDER BY {sort_column} {sort_order}
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset]
    )

    patients = cursor.fetchall()

    conn.close()

    patient_list = []

    for patient in patients:
        patient_list.append({
            "id": patient["id"],
            "name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "email": patient["email"],
            "phone": patient["phone"]
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


# =========================================================
# STEP 13 + 14 + 15 - CREATE APPOINTMENT
# =========================================================

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

    required_fields = [
        doctor_id,
        patient_name,
        patient_phone,
        patient_email,
        start_at,
        end_at
    ]

    if any(value is None or value == "" for value in required_fields):
        return jsonify({
            "error": "All appointment fields are required"
        }), 400

    try:
        start_datetime = datetime.fromisoformat(start_at)
        end_datetime = datetime.fromisoformat(end_at)
    except ValueError:
        return jsonify({
            "error": "Invalid date/time format. Use YYYY-MM-DDTHH:MM"
        }), 400

    if end_datetime <= start_datetime:
        return jsonify({
            "error": "end_at must be after start_at"
        }), 400

    conn = get_db_connection()

    try:
        # STEP 15 - CONCURRENCY SAFETY

        conn.execute("BEGIN IMMEDIATE")

        cursor = conn.cursor()

        # -------------------------------------------------
        # CHECK DOCTOR
        # -------------------------------------------------

        cursor.execute("""
            SELECT id, name
            FROM doctors
            WHERE id = ?
        """, (doctor_id,))

        doctor = cursor.fetchone()

        if not doctor:
            conn.rollback()

            return jsonify({
                "error": "Doctor not found"
            }), 404

        # -------------------------------------------------
        # STEP 14 - CHECK OVERLAPPING APPOINTMENT
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM appointments
            WHERE doctor_id = ?
              AND status NOT IN ('Cancelled', 'Canceled')
              AND start_at IS NOT NULL
              AND end_at IS NOT NULL
              AND start_at < ?
              AND end_at > ?
            LIMIT 1
        """, (
            doctor_id,
            end_at,
            start_at
        ))

        conflict = cursor.fetchone()

        if conflict:
            conn.rollback()

            return jsonify({
                "error": "This doctor already has an overlapping appointment"
            }), 409

        # -------------------------------------------------
        # FIND PATIENT BY EMAIL
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM patients
            WHERE email = ?
        """, (patient_email,))

        patient = cursor.fetchone()

        if patient:
            patient_id = patient["id"]

        else:
            # -------------------------------------------------
            # FIND PATIENT BY PHONE
            # -------------------------------------------------

            cursor.execute("""
                SELECT id
                FROM patients
                WHERE phone = ?
            """, (patient_phone,))

            patient = cursor.fetchone()

            if patient:
                patient_id = patient["id"]

            else:
                # -------------------------------------------------
                # CREATE NEW PATIENT
                # -------------------------------------------------

                cursor.execute("""
                    INSERT INTO patients
                    (name, email, phone)
                    VALUES (?, ?, ?)
                """, (
                    patient_name,
                    patient_email,
                    patient_phone
                ))

                patient_id = cursor.lastrowid

        # -------------------------------------------------
        # CREATE APPOINTMENT
        # -------------------------------------------------

        appointment_date = start_datetime.strftime("%Y-%m-%d")
        appointment_time = start_datetime.strftime("%H:%M")

        cursor.execute("""
            INSERT INTO appointments
            (
                doctor_id,
                patient_id,
                appointment_date,
                appointment_time,
                status,
                start_at,
                end_at,
                cancellation_fee,
                cancelled_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doctor_id,
            patient_id,
            appointment_date,
            appointment_time,
            "Pending",
            start_at,
            end_at,
            0,
            None
        ))

        appointment_id = cursor.lastrowid

        conn.commit()

        # -------------------------------------------------
        # GET CREATED APPOINTMENT
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                a.id,
                a.doctor_id,
                a.patient_id,
                p.name AS patient_name,
                p.phone AS patient_phone,
                p.email AS patient_email,
                a.start_at,
                a.end_at,
                a.status
            FROM appointments a
            JOIN patients p
                ON a.patient_id = p.id
            WHERE a.id = ?
        """, (appointment_id,))

        appointment = cursor.fetchone()

        return jsonify({
            "message": "Appointment booked successfully",
            "appointment": {
                "id": appointment["id"],
                "doctor_id": appointment["doctor_id"],
                "patient_id": appointment["patient_id"],
                "patient_name": appointment["patient_name"],
                "patient_phone": appointment["patient_phone"],
                "patient_email": appointment["patient_email"],
                "start_at": appointment["start_at"],
                "end_at": appointment["end_at"],
                "status": appointment["status"]
            }
        }), 201

    except sqlite3.Error as e:
        conn.rollback()

        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500

    finally:
        conn.close()


# =========================================================
# STEP 17 - CANCEL APPOINTMENT
# =========================================================

@app.route("/api/appointments/<int:appointment_id>/cancel", methods=["POST"])
def cancel_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                start_at,
                status
            FROM appointments
            WHERE id = ?
        """, (appointment_id,))

        appointment = cursor.fetchone()

        if not appointment:
            return jsonify({
                "error": "Appointment not found"
            }), 404

        if appointment["status"] in ("Cancelled", "Canceled"):
            return jsonify({
                "error": "Appointment is already cancelled"
            }), 400

        if not appointment["start_at"]:
            return jsonify({
                "error": "Appointment start time is missing"
            }), 400

        appointment_start = datetime.fromisoformat(
            appointment["start_at"]
        )

        current_time = datetime.now()

        hours_remaining = (
            appointment_start - current_time
        ).total_seconds() / 3600

        # 24 hours or more -> ₹0
        # Less than 24 hours -> ₹200

        if hours_remaining >= 24:
            cancellation_fee = 0
        else:
            cancellation_fee = 200

        cancelled_at = current_time.isoformat()

        cursor.execute("""
            UPDATE appointments
            SET
                status = 'Cancelled',
                cancellation_fee = ?,
                cancelled_at = ?
            WHERE id = ?
        """, (
            cancellation_fee,
            cancelled_at,
            appointment_id
        ))

        conn.commit()

        return jsonify({
            "message": "Appointment cancelled successfully",
            "appointment_id": appointment_id,
            "status": "Cancelled",
            "cancellation_fee": cancellation_fee,
            "cancelled_at": cancelled_at
        }), 200

    except sqlite3.Error as e:
        conn.rollback()

        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500

    finally:
        conn.close()


# =========================================================
# STEP 19 - APPOINTMENT LISTING
# =========================================================

@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    date = request.args.get("date")
    doctor_id = request.args.get("doctor_id")
    patient = request.args.get("patient")
    status = request.args.get("status")

    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(
            max(int(request.args.get("limit", 10)), 1),
            100
        )
    except ValueError:
        return jsonify({
            "error": "page and limit must be integers"
        }), 400

    sort = request.args.get("sort", "start_at")
    order = request.args.get("order", "asc").lower()

    allowed_sort_fields = {
        "id": "a.id",
        "start_at": "a.start_at",
        "end_at": "a.end_at",
        "status": "a.status",
        "doctor": "d.name",
        "patient": "p.name"
    }

    if sort not in allowed_sort_fields:
        return jsonify({
            "error": "Invalid sort field"
        }), 400

    if order not in ("asc", "desc"):
        return jsonify({
            "error": "order must be asc or desc"
        }), 400

    conn = get_db_connection()

    try:
        # -------------------------------------------------
        # MAIN APPOINTMENT QUERY
        # -------------------------------------------------

        query = """
            SELECT
                a.id,
                a.doctor_id,
                d.name AS doctor_name,
                d.specialization,
                a.patient_id,
                p.name AS patient_name,
                p.phone AS patient_phone,
                p.email AS patient_email,
                a.appointment_date,
                a.appointment_time,
                a.start_at,
                a.end_at,
                a.status,
                a.cancellation_fee,
                a.cancelled_at
            FROM appointments a
            JOIN doctors d
                ON a.doctor_id = d.id
            JOIN patients p
                ON a.patient_id = p.id
            WHERE 1=1
        """

        params = []

        # -------------------------------------------------
        # FILTER BY DATE
        # -------------------------------------------------

        if date:
            query += " AND a.appointment_date = ?"
            params.append(date)

        # -------------------------------------------------
        # FILTER BY DOCTOR
        # -------------------------------------------------

        if doctor_id:
            try:
                doctor_id = int(doctor_id)
            except ValueError:
                conn.close()

                return jsonify({
                    "error": "doctor_id must be an integer"
                }), 400

            query += " AND a.doctor_id = ?"
            params.append(doctor_id)

        # -------------------------------------------------
        # SEARCH PATIENT
        # -------------------------------------------------

        if patient:
            query += """
                AND (
                    p.name LIKE ?
                    OR p.phone LIKE ?
                    OR p.email LIKE ?
                )
            """

            patient_search = f"%{patient}%"

            params.extend([
                patient_search,
                patient_search,
                patient_search
            ])

        # -------------------------------------------------
        # FILTER BY STATUS
        # -------------------------------------------------

        if status:
            query += " AND a.status = ?"
            params.append(status)

        # -------------------------------------------------
        # SORTING
        # -------------------------------------------------

        query += (
            f" ORDER BY "
            f"{allowed_sort_fields[sort]} "
            f"{order.upper()}"
        )

        # -------------------------------------------------
        # PAGINATION
        # -------------------------------------------------

        offset = (page - 1) * limit

        query += " LIMIT ? OFFSET ?"

        params.extend([
            limit,
            offset
        ])

        rows = conn.execute(
            query,
            params
        ).fetchall()

        # -------------------------------------------------
        # COUNT TOTAL RESULTS
        # -------------------------------------------------

        count_query = """
            SELECT COUNT(*)
            FROM appointments a
            JOIN doctors d
                ON a.doctor_id = d.id
            JOIN patients p
                ON a.patient_id = p.id
            WHERE 1=1
        """

        count_params = []

        if date:
            count_query += " AND a.appointment_date = ?"
            count_params.append(date)

        if doctor_id:
            count_query += " AND a.doctor_id = ?"
            count_params.append(doctor_id)

        if patient:
            count_query += """
                AND (
                    p.name LIKE ?
                    OR p.phone LIKE ?
                    OR p.email LIKE ?
                )
            """

            patient_search = f"%{patient}%"

            count_params.extend([
                patient_search,
                patient_search,
                patient_search
            ])

        if status:
            count_query += " AND a.status = ?"
            count_params.append(status)

        total = conn.execute(
            count_query,
            count_params
        ).fetchone()[0]

        # -------------------------------------------------
        # FORMAT RESPONSE
        # -------------------------------------------------

        appointments = []

        for row in rows:
            appointments.append({
                "id": row["id"],
                "doctor_id": row["doctor_id"],
                "doctor_name": row["doctor_name"],
                "specialization": row["specialization"],
                "patient_id": row["patient_id"],
                "patient_name": row["patient_name"],
                "patient_phone": row["patient_phone"],
                "patient_email": row["patient_email"],
                "appointment_date": row["appointment_date"],
                "appointment_time": row["appointment_time"],
                "start_at": row["start_at"],
                "end_at": row["end_at"],
                "status": row["status"],
                "cancellation_fee": row["cancellation_fee"],
                "cancelled_at": row["cancelled_at"]
            })

        total_pages = (total + limit - 1) // limit

        return jsonify({
            "appointments": appointments,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500

    finally:
        conn.close()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    create_database()
    app.run(debug=True)