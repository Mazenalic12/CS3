#!/usr/bin/env python3
"""
Innovatech HR Self-Service Portal (MVP)

- HR kan een medewerker zoeken op e-mail en details zien.
- HR kan een nieuwe medewerker toevoegen via een formulier.
- Bij het toevoegen wordt de volledige onboarding direct uitgevoerd:
  * record in de employees-tabel
  * status = ACTIVE
  * cloud_account_created = TRUE
  * workspace_username + tijdelijk wachtwoord worden gegenereerd
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, render_template_string, redirect, url_for
import string
import secrets
import datetime
import subprocess


app = Flask(__name__)

# Database connection settings from environment variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hr_employees")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    return conn


def generate_workspace_username(email: str) -> str:
    # voorbeeld: giovanni.hr@innovatech.com -> giovanni_hr
    local_part = email.split("@")[0]
    return local_part.replace(".", "_")


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


INDEX_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Innovatech HR Portal</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      h1 { font-size: 1.8rem; }
      form { margin-bottom: 1.5rem; }
      label { font-weight: bold; }
      input[type="text"] { padding: 0.3rem; width: 300px; }
      input[type="submit"], a.button {
        padding: 0.3rem 0.8rem;
        text-decoration: none;
        border: 1px solid #ccc;
        background-color: #f5f5f5;
        color: #000;
        margin-right: 0.5rem;
      }
      table { border-collapse: collapse; margin-top: 1rem; }
      th, td { border: 1px solid #ccc; padding: 0.4rem 0.8rem; }
      th { background-color: #f5f5f5; text-align: left; }
      .message { margin-top: 1rem; color: #555; }
    </style>
  </head>
  <body>
    <h1>Innovatech HR Self-Service Portal</h1>

    <p>
      <a href="{{ url_for('add_employee') }}" class="button">+ Add employee</a>
    </p>

    <form method="get" action="/">
      <label for="email">Employee email:</label><br>
      <input type="text" id="email" name="email" value="{{ email or '' }}" placeholder="user@innovatech.com">
      <input type="submit" value="Search">
    </form>

    {% if employee %}
      <h2>Employee details</h2>
      <table>
        <tr><th>Name</th><td>{{ employee.name }}</td></tr>
        <tr><th>Email</th><td>{{ employee.email }}</td></tr>
        <tr><th>Department</th><td>{{ employee.department }}</td></tr>
        <tr><th>Role</th><td>{{ employee.role }}</td></tr>
        <tr><th>Status</th><td>{{ employee.status }}</td></tr>
        <tr><th>Cloud account created</th><td>{{ employee.cloud_account_created }}</td></tr>
        <tr><th>Deprovisioned</th><td>{{ employee.deprovisioned }}</td></tr>
        <tr><th>Device enrolled</th><td>{{ employee.device_enrolled }}</td></tr>
        <tr><th>Workspace username</th><td>{{ employee.workspace_username or '-' }}</td></tr>
        <tr><th>Workspace temp password</th><td>{{ employee.workspace_temp_password or '-' }}</td></tr>
        <tr><th>Last action</th><td>{{ employee.last_action or '-' }}</td></tr>
      </table>
    {% elif email %}
      <div class="message">
        No employee found for email <strong>{{ email }}</strong>.
      </div>
    {% else %}
      <div class="message">
        Enter an Innovatech email address to view the employee record from the HR database.
      </div>
    {% endif %}
  </body>
</html>
"""

ADD_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Add employee - Innovatech HR Portal</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      h1 { font-size: 1.6rem; }
      form { margin-top: 1rem; max-width: 400px; }
      label { font-weight: bold; display: block; margin-top: 0.5rem; }
      input[type="text"], select {
        padding: 0.3rem;
        width: 100%;
      }
      input[type="submit"], a.button {
        margin-top: 1rem;
        padding: 0.3rem 0.8rem;
        text-decoration: none;
        border: 1px solid #ccc;
        background-color: #f5f5f5;
        color: #000;
      }
    </style>
  </head>
  <body>
    <h1>Add new employee</h1>

    <form method="post" action="{{ url_for('add_employee') }}">
      <label for="name">Full name</label>
      <input type="text" id="name" name="name" required>

      <label for="email">Email address</label>
      <input type="text" id="email" name="email" required placeholder="user@innovatech.com">

      <label for="department">Department</label>
      <input type="text" id="department" name="department" required>

      <label for="role">Role</label>
      <select id="role" name="role" required>
        <option value="Employee">Employee</option>
        <option value="Manager">Manager</option>
        <option value="HR_Admin">HR_Admin</option>
      </select>

      <input type="submit" value="Create and onboard employee">
      <a href="{{ url_for('index') }}" class="button">Cancel</a>
    </form>
  </body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    email = request.args.get("email", "").strip()
    employee = None

    if email:
        conn = get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, name, email, department, role, status,
                           cloud_account_created, deprovisioned,
                           device_enrolled, workspace_username,
                           workspace_temp_password, last_action
                    FROM employees
                    WHERE email = %s;
                    """,
                    (email,),
                )
                employee = cur.fetchone()
        finally:
            conn.close()

    return render_template_string(INDEX_TEMPLATE, email=email, employee=employee)


@app.route("/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "GET":
        return render_template_string(ADD_TEMPLATE)

    # POST: form submit -> volledige onboarding in één stap
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    department = request.form.get("department", "").strip()
    role = request.form.get("role", "").strip()

    if not name or not email or not department or not role:
        return render_template_string(ADD_TEMPLATE)

    # Workspace credentials genereren
    workspace_username = generate_workspace_username(email)
    workspace_password = generate_temp_password()
    when = datetime.datetime.utcnow().isoformat() + "Z"
    action_text = f"Onboarding completed at {when}"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO employees (name, email, department, role, status)
                VALUES (%s, %s, %s, %s, 'NEW');
                """,
                (name, email, department, role),
            )
        conn.commit()
    finally:
        conn.close()

    # onboarding.py automatisch starten
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    onboarding_script = os.path.join(project_root, "automation", "onboarding.py")
    subprocess.Popen(["python", onboarding_script])

    print(f"[PORTAL] Created NEW employee {email}, onboarding.py started")

    # Na toevoegen ga terug naar detailpagina van deze employee
    return redirect(url_for("index", email=email))



if __name__ == "__main__":
    # Dev-run: in Cloud Shell / lokaal
    app.run(host="0.0.0.0", port=8080, debug=True)
