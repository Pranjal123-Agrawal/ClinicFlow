from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

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

    # Add sample doctors only if the table is empty
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

    # Check required fields
    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    # Check password length
    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if email already exists
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

    # Hash password before storing it
    password_hash = generate_password_hash(password)

    # Insert user
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

    # Check required fields
    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Find user by email
    cursor.execute("""
        SELECT id, name, email, password, role
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()

    # User does not exist
    if not user:
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    user_id, name, user_email, password_hash, role = user

    # Check password against stored hash
    if not check_password_hash(password_hash, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    # Create login session
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


if __name__ == "__main__":
    create_database()
    app.run(debug=True)