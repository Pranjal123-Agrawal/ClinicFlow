# ClinicFlow

## Overview

ClinicFlow is a small-clinic appointment workspace. It helps receptionists and front desk staff find patients, manage doctor schedules, prevent overlapping bookings, and apply cancellation fees consistently.

## Features

- Landing page explaining the product and roadmap
- Staff registration and login
- Dashboard with today's appointments, cancellations, and doctors
- Appointment booking with backend conflict prevention
- Appointment search, doctor/date filters, sorting, pagination, and cancellation
- Patient search by name, phone, or email with sorting and pagination
- Responsive UI for desktop and mobile

## Tech Stack

- Python and Flask REST API
- SQLite relational database
- Vanilla HTML, CSS, and JavaScript frontend
- Werkzeug password hashing

## Database Design

The database contains `users`, `doctors`, `patients`, and `appointments` tables. Appointments reference both doctors and patients through foreign keys and store `start_at`, `end_at`, status, cancellation fee, and cancellation time.

## How to Run

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser. The first run creates `clinic.db` and seeds three doctors.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Serves the frontend |
| POST | `/api/register` | Creates a staff user |
| POST | `/api/login` | Starts a staff session |
| GET | `/api/doctors` | Lists available doctors |
| GET | `/api/patients` | Searches and paginates patients |
| POST | `/api/appointments` | Books an appointment and creates or reuses a patient |
| GET | `/api/appointments` | Filters, sorts, and paginates appointments |
| POST | `/api/appointments/<id>/cancel` | Cancels an appointment and calculates its fee |

## Conflict Prevention

The backend starts an immediate SQLite transaction, then checks whether the same doctor has an active appointment where `existing_start < requested_end` and `existing_end > requested_start`. A conflict returns HTTP `409`, so frontend checks cannot bypass the rule.

## Cancellation Rule

Cancellation at least 24 hours before the appointment costs `0`. Cancellation within 24 hours costs `200`. The backend stores the fee and cancellation timestamp with the appointment.

## Search

Patient search accepts `q` and matches patient name, email, or phone. Appointment search accepts `patient` and matches the same three fields.

## Pagination

Both listing endpoints accept `page` and `limit`, and return `total` and `total_pages` metadata. Appointment limits are capped at 100 by the API.

## Sorting

Patients support `name`, `age`, `gender`, `email`, and `phone`. Appointments support `id`, `start_at`, `end_at`, `status`, `doctor`, and `patient`, with `asc` or `desc` ordering.

## Testing

Run the syntax checks:

```bash
python -m py_compile app.py
node --check static/app.js
```

Then run `python app.py` and verify: register, login, open the dashboard, book a first appointment, attempt an overlapping appointment and confirm the conflict message, book a non-overlapping appointment, search the patient, filter the doctor's schedule, and cancel an appointment to inspect its fee.

## Future Improvements

SMS reminders, online payments, doctor leave and working-hours management, role-based permissions, and automated API tests.