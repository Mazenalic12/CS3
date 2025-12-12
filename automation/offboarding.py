#!/usr/bin/env python3
"""
Offboarding Automation Service (prototype)

- Selects employees with status = 'INACTIVE' and deprovisioned = false
- Simulates disabling the cloud identity account and removing group access
- Updates the employees table:
    deprovisioned = true
    last_action = 'Offboarding completed at ...'
    updated_at = NOW()
"""

import os
import sys
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Optional Prometheus metrics (safe fallback if library is missing)
try:
    from prometheus_client import Counter
except ImportError:  # pragma: no cover - optional dependency
    Counter = None

# Same env vars as onboarding.py
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hr_employees")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Prometheus-style counters (optional; only active when prometheus_client is installed)
if Counter is not None:
    OFFBOARDING_ATTEMPTS = Counter(
        "automation_offboarding_attempts_total",
        "Number of employees processed by the offboarding service",
        ["result"],
    )
else:
    OFFBOARDING_ATTEMPTS = None


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


def fetch_employees_to_offboard(conn):
    """Get all employees that must be deprovisioned."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, name, email, department, role
            FROM employees
            WHERE status = 'INACTIVE'
              AND deprovisioned = FALSE
            ORDER BY id;
            """
        )
        return cur.fetchall()


def _groups_for_role(role: str):
    """Return the logical access groups for a given business role."""
    base_groups = ["corp-all-employees"]
    role_norm = (role or "Employee").strip().upper()

    if role_norm == "MANAGER":
        base_groups.append("corp-managers")
    elif role_norm in {"HR_ADMIN", "HR-ADMIN", "HR ADMIN"}:
        base_groups.append("corp-hr-admins")

    return base_groups


def simulate_cloud_identity_offboarding(employee):
    """
    Simulate the Cloud Identity offboarding.

    In a real implementation this function would:
    - disable the user in Cloud Identity
    - remove the user from all access groups
    """
    email = employee.get("email")
    role = employee.get("role", "Employee")
    groups = _groups_for_role(role)

    print(f"[OFFBOARD] Disabling cloud identity account for {email}")
    print(f"[OFFBOARD] Revoking active sessions / tokens for {email}")

    for g in groups:
        print(f"[OFFBOARD] Removing {email} from group {g}")


def mark_employee_as_offboarded(conn, employee_id):
    """Update employee record after successful offboarding."""
    now = datetime.datetime.utcnow()
    action_text = f"Offboarding completed at {now.isoformat()}Z"

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE employees
            SET deprovisioned = TRUE,
                last_action = %s,
                updated_at = NOW()
            WHERE id = %s;
            """,
            (action_text, employee_id),
        )


def main():
    print("=== Offboarding run started ===")
    conn = get_db_connection()
    try:
        with conn:
            employees = fetch_employees_to_offboard(conn)
            if not employees:
                print("No employees with status INACTIVE to offboard.")
                return

            print(f"Found {len(employees)} employee(s) to offboard.")
            for emp in employees:
                print(f"\nProcessing employee ID {emp['id']} - {emp['email']}")
                try:
                    simulate_cloud_identity_offboarding(emp)
                    mark_employee_as_offboarded(conn, emp["id"])
                except Exception as e:
                    print(f"[ERROR] Failed to offboard {emp['email']}: {e}")
                    if OFFBOARDING_ATTEMPTS is not None:
                        OFFBOARDING_ATTEMPTS.labels(result="error").inc()
                    continue

                print("[OK] Employee marked as deprovisioned in database.")
                if OFFBOARDING_ATTEMPTS is not None:
                    OFFBOARDING_ATTEMPTS.labels(result="success").inc()

        print("\n=== Offboarding run finished successfully ===")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
