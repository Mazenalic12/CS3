#!/usr/bin/env python3
"""
Onboarding Automation Service (prototype)

- Selects employees with status = 'NEW' and cloud_account_created = false
- Simulates creation of a cloud identity account and group assignment
- Updates the employees table:
    status = 'ACTIVE'
    cloud_account_created = true
    last_action = 'Onboarding completed at ...'
    updated_at = NOW()
"""

import os
import sys
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


# Read DB connection settings from environment variables
DB_HOST = os.getenv("DB_HOST")      # e.g. private IP of hr-postgres-db
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hr_employees")
DB_USER = os.getenv("DB_USER")      # e.g. hr_app_user
DB_PASSWORD = os.getenv("DB_PASSWORD")  # your db password


def get_db_connection():
    """Create a PostgreSQL connection."""
    missing = [name for name, value in [
        ("DB_HOST", DB_HOST),
        ("DB_USER", DB_USER),
        ("DB_PASSWORD", DB_PASSWORD),
    ] if not value]

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    return conn


def fetch_new_employees(conn):
    """Get all employees that need onboarding."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, name, email, department, role
            FROM employees
            WHERE status = 'NEW'
              AND cloud_account_created = FALSE
            ORDER BY id;
            """
        )
        return cur.fetchall()


def simulate_cloud_identity_onboarding(employee):
    """
    Simulate the Cloud Identity calls.

    In a real implementation this function would:
    - create a user in Cloud Identity
    - add the user to groups based on role (hr-admins, hr-managers, employees)
    """
    print(f"[ONBOARD] Creating cloud identity account for {employee['email']}")
    if employee["role"] == "HR_Admin":
        group = "hr-admins"
    elif employee["role"] == "Manager":
        group = "hr-managers"
    else:
        group = "employees"

    print(f"[ONBOARD] Adding {employee['email']} to group: {group}")
    # Here you would call the Admin SDK / Cloud Identity API


def mark_employee_as_onboarded(conn, employee_id):
    """Update employee record after successful onboarding."""
    now = datetime.datetime.utcnow()
    action_text = f"Onboarding completed at {now.isoformat()}Z"

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE employees
            SET status = 'ACTIVE',
                cloud_account_created = TRUE,
                last_action = %s,
                updated_at = NOW()
            WHERE id = %s;
            """,
            (action_text, employee_id),
        )


def main():
    print("=== Onboarding run started ===")
    conn = get_db_connection()
    try:
        with conn:
            employees = fetch_new_employees(conn)
            if not employees:
                print("No employees with status NEW found.")
                return

            print(f"Found {len(employees)} employee(s) to onboard.")
            for emp in employees:
                print(f"\nProcessing employee ID {emp['id']} - {emp['email']}")
                simulate_cloud_identity_onboarding(emp)
                mark_employee_as_onboarded(conn, emp["id"])
                print("[OK] Employee marked as ACTIVE in database.")

        print("\n=== Onboarding run finished successfully ===")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
