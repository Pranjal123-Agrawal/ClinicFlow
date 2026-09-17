# REASONING

## Problem Understanding

Small clinics need a quick way to manage appointments without relying on memory or a spreadsheet. The most important risk is double-booking a doctor while the front desk is moving quickly.

## Product Decisions

The frontend is organized around the daily workflow: dashboard, book appointment, appointments, and patients. The conflict message is visible in the booking workspace so the core value is easy to evaluate.

## Technology Choice

I chose SQLite because the assessment is time-limited and SQLite provides real persistent relational storage without requiring a separate database server. Flask keeps the REST API small and easy to run.

## Database Design

Users, doctors, patients, and appointments are separate tables. Appointments use foreign keys and store both the human-readable appointment date/time and ISO start/end values for overlap checks.

## Conflict Prevention

The conflict check is performed by the backend because frontend validation alone cannot guarantee database consistency. `BEGIN IMMEDIATE` makes the check and insert safe from competing writes in SQLite.

## Cancellation Rule

The backend calculates the fee from the appointment start time: 0 when at least 24 hours remain, otherwise 200. This keeps the policy consistent across all clients.

## Search Design

Patient and appointment search use parameterized `LIKE` filters across name, phone, and email. Sort fields are allowlisted before being interpolated into SQL.

## Pagination and Sorting

Both list APIs return records plus pagination metadata. Sort values and directions are validated against allowlists so the frontend can offer simple controls without exposing arbitrary SQL.

## Testing

Python and JavaScript syntax checks were run. The intended manual flow is registration, login, dashboard, two overlapping booking attempts, a successful non-overlapping booking, patient search, doctor filtering, and cancellation fee verification.

## Bugs Found

The original frontend buttons only changed the URL and displayed placeholder alerts. The documentation files were also empty.

## Fixes

Replaced the placeholder page with a responsive landing page and authenticated workspace. Added API-backed loading, forms, conflict feedback, table filters, pagination, patient lookup, cancellation actions, and project documentation.

## Future Improvements

Add automated Flask client tests, stronger production session configuration, SMS reminders, online payments, and working-hours validation.
