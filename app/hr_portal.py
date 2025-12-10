#!/usr/bin/env python3
"""
Simple HR Self-Service Portal (MVP)

- Shows basic employee information from the 'employees' table in Cloud SQL.
- Employee is selected by email address (as query parameter or form input).
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Database connection settings from environment variables
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hr_employees")
DB_USER = os.getenv("hr_app_user")
DB_PASSWORD = os.getenv("12345")


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    return conn


HTML_TEMPLATE = """
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
      input[type="submit"] { padding: 0.3rem 0.8rem; }
      table { border-collapse: collapse; margin-top: 1rem; }
      th, td { border: 1px solid #ccc; padding: 0.4rem 0.8rem; }
      th { background-color: #f5f5f5; text-align: left; }
      .message { margin-top: 1rem; color: #555; }
    </style>
  </head>
  <body>
    <h1>Innovatech HR Self-Service Portal</h1>

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
                           device_enrolled, last_action
                    FROM employees
                    WHERE email = %s;
                    """,
                    (email,),
                )
                row = cur.fetchone()
                employee = row
        finally:
            conn.close()

    return render_template_string(HTML_TEMPLATE, email=email, employee=employee)


if __name__ == "__main__":
    # For local/dev use only – in Kubernetes this will be run by gunicorn or similar
    app.run(host="0.0.0.0", port=8080, debug=True)
