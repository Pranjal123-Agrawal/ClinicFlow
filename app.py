from flask import Flask
import sqlite3

app = Flask(__name__)

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


if __name__ == "__main__":
    create_database()
    app.run(debug=True)