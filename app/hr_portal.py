#!/usr/bin/env python3


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


# ---------- TEMPLATES ----------

INDEX_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Innovatech HR Portal</title>
    <style>
      :root {
        --primary: #2563eb;
        --primary-light: #dbeafe;
        --primary-dark: #1d4ed8;
        --danger: #ef4444;
        --bg: #f3f4f6;
        --card-bg: #ffffff;
        --border: #e5e7eb;
        --text-main: #111827;
        --text-muted: #6b7280;
      }

      * { box-sizing: border-box; }

      body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        padding: 0;
        background: radial-gradient(circle at top, #e0f2fe 0, #f9fafb 45%, #eef2ff 100%);
        color: var(--text-main);
      }

      .container {
        max-width: 960px;
        margin: 2rem auto 3rem;
        padding: 0 1.5rem;
      }

      .shell {
        background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(239,246,255,0.95));
        border-radius: 1rem;
        box-shadow:
          0 10px 25px rgba(15, 23, 42, 0.08),
          0 0 0 1px rgba(148, 163, 184, 0.3);
        padding: 1.5rem 2rem 2rem;
      }

      header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1.5rem;
      }

      .title-block h1 {
        margin: 0;
        font-size: 1.6rem;
        letter-spacing: -0.03em;
      }

      .title-block p {
        margin: 0.25rem 0 0;
        font-size: 0.9rem;
        color: var(--text-muted);
      }

      nav { display: flex; gap: 0.5rem; }

      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.4rem 0.9rem;
        border-radius: 999px;
        border: 1px solid transparent;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
        transition: background 120ms ease, color 120ms ease,
                    transform 80ms ease, box-shadow 80ms ease;
        white-space: nowrap;
      }

      .btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.15);
      }

      .btn:active {
        transform: translateY(0);
        box-shadow: none;
      }

      .btn-primary {
        background: radial-gradient(circle at top left, var(--primary-light), var(--primary));
        color: #ffffff;
      }

      .btn-primary:hover {
        background: radial-gradient(circle at top left, var(--primary-light), var(--primary-dark));
      }

      .btn-secondary {
        background: rgba(255, 255, 255, 0.8);
        border-color: var(--border);
        color: var(--text-main);
      }

      .btn-secondary:hover { background: #f9fafb; }

      .btn-danger {
        background: radial-gradient(circle at top left, #fee2e2, var(--danger));
        color: #111827;
      }

      .btn-danger:hover {
        background: radial-gradient(circle at top left, #fecaca, #b91c1c);
      }

      .layout {
        display: grid;
        grid-template-columns: minmax(0, 1.2fr) minmax(0, 1.5fr);
        gap: 1.75rem;
      }

      @media (max-width: 840px) {
        .shell { padding: 1.2rem 1.3rem 1.5rem; }
        .layout { grid-template-columns: minmax(0, 1fr); }
        header { flex-direction: column; align-items: flex-start; }
        nav { width: 100%; justify-content: flex-start; flex-wrap: wrap; }
      }

      .card {
        background: var(--card-bg);
        border-radius: 0.9rem;
        border: 1px solid var(--border);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        padding: 1rem 1.2rem 1.1rem;
      }

      .card h2 { margin: 0 0 0.75rem; font-size: 1.05rem; }

      form.search-form {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
      }

      label {
        font-weight: 600;
        font-size: 0.85rem;
      }

      input[type="text"] {
        padding: 0.45rem 0.6rem;
        border-radius: 0.6rem;
        border: 1px solid var(--border);
        font-size: 0.9rem;
        width: 100%;
      }

      input[type="text"]:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 1px var(--primary-light);
      }

      .helper {
        font-size: 0.78rem;
        color: var(--text-muted);
      }

      .actions-inline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-top: 0.75rem;
        flex-wrap: wrap;
      }

      .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }

      .status-new      { background: #eff6ff; color: #1d4ed8; }
      .status-active   { background: #ecfdf5; color: #047857; }
      .status-inactive { background: #fef2f2; color: #b91c1c; }

      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 0.5rem;
        font-size: 0.88rem;
      }

      th, td {
        border-bottom: 1px solid #e5e7eb;
        padding: 0.45rem 0.4rem;
        text-align: left;
      }

      th {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
      }

      tr:last-child td { border-bottom: none; }

      .field-name {
        width: 32%;
        color: var(--text-muted);
        font-weight: 500;
      }

      .message {
        margin-top: 0.4rem;
        font-size: 0.86rem;
        color: var(--text-muted);
      }

      .message strong { color: var(--text-main); }

      .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 500;
        background: #f3f4f6;
        color: #374151;
      }

      .pill-true  { background: #dcfce7; color: #166534; }
      .pill-false { background: #fee2e2; color: #b91c1c; }

      .last-action {
        max-width: 22rem;
        white-space: normal;
        word-break: break-word;
      }

      .muted-note {
        font-size: 0.8rem;
        color: var(--text-muted);
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="shell">
        <header>
          <div class="title-block">
            <h1>Innovatech HR Self-Service Portal</h1>
            <p>Zoek medewerkers, start onboarding &amp; offboarding vanuit één plek.</p>
          </div>
          <nav>
            <a href="{{ url_for('add_employee') }}" class="btn btn-primary">+ Add employee</a>
            <a href="{{ url_for('list_employees') }}" class="btn btn-secondary">View all employees</a>
          </nav>
        </header>

        <div class="layout">
          <section class="card">
            <h2>Find employee</h2>
            <form class="search-form" method="get" action="{{ url_for('index') }}">
              <div>
                <label for="email">Employee email</label>
                <input type="text" id="email" name="email" value="{{ email or '' }}" placeholder="user@innovatech.com">
                <p class="helper">Type een Innovatech-adres en druk op Enter om de details te zien.</p>
              </div>
              <div>
                <button type="submit" class="btn btn-secondary">Search</button>
              </div>
            </form>
          </section>

          <section class="card">
            <h2>Employee details</h2>
            {% if employee %}
              <div class="actions-inline">
                <div>
                  <span class="status-pill status-{{ employee.status|lower }}">
                    {{ employee.status }}
                  </span>
                </div>

                <div>
                  {% if employee.status != 'INACTIVE' and not employee.deprovisioned %}
                    <form method="post"
                          action="{{ url_for('offboard_employee', employee_id=employee.id) }}"
                          style="display:inline;"
                          onsubmit="return confirm('Offboard {{ employee.name }}? Dit markeert de gebruiker als INACTIVE en start het offboarding-script.');">
                      <button type="submit" class="btn btn-danger">Start offboarding</button>
                    </form>
                  {% elif employee.deprovisioned %}
                    <span class="muted-note">Employee is al volledig offboarded.</span>
                  {% else %}
                    <span class="muted-note">Employee is INACTIVE; offboarding loopt of is klaar.</span>
                  {% endif %}
                </div>
              </div>

              <table>
                <tr><th class="field-name">Name</th><td>{{ employee.name }}</td></tr>
                <tr><th class="field-name">Email</th><td>{{ employee.email }}</td></tr>
                <tr><th class="field-name">Department</th><td>{{ employee.department }}</td></tr>
                <tr><th class="field-name">Role</th><td>{{ employee.role }}</td></tr>
                <tr>
                  <th class="field-name">Cloud account created</th>
                  <td>
                    <span class="pill pill-{{ 'true' if employee.cloud_account_created else 'false' }}">
                      {{ 'Yes' if employee.cloud_account_created else 'No' }}
                    </span>
                  </td>
                </tr>
                <tr>
                  <th class="field-name">Device enrolled</th>
                  <td>
                    <span class="pill pill-{{ 'true' if employee.device_enrolled else 'false' }}">
                      {{ 'Yes' if employee.device_enrolled else 'No' }}
                    </span>
                  </td>
                </tr>
                <tr>
                  <th class="field-name">Deprovisioned</th>
                  <td>
                    <span class="pill pill-{{ 'true' if employee.deprovisioned else 'false' }}">
                      {{ 'Yes' if employee.deprovisioned else 'No' }}
                    </span>
                  </td>
                </tr>
                <tr><th class="field-name">Workspace username</th><td>{{ employee.workspace_username or '-' }}</td></tr>
                <tr><th class="field-name">Workspace temp password</th><td>{{ employee.workspace_temp_password or '-' }}</td></tr>
                <tr><th class="field-name">Last action</th><td class="last-action">{{ employee.last_action or '-' }}</td></tr>
              </table>
            {% elif email %}
              <p class="message">
                No employee found for email <strong>{{ email }}</strong>.
              </p>
            {% else %}
              <p class="message">
                Enter an Innovatech email address to view the employee record,
                of gebruik <strong>View all employees</strong> om de volledige lijst te zien.
              </p>
            {% endif %}
          </section>
        </div>
      </div>
    </div>
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
      body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        padding: 0;
        background: radial-gradient(circle at top, #e0f2fe 0, #f9fafb 45%, #eef2ff 100%);
      }

      .container {
        max-width: 640px;
        margin: 2.5rem auto;
        padding: 0 1.5rem;
      }

      .card {
        background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(239,246,255,0.98));
        border-radius: 1rem;
        padding: 1.6rem 1.8rem 1.8rem;
        box-shadow:
          0 10px 25px rgba(15, 23, 42, 0.08),
          0 0 0 1px rgba(148, 163, 184, 0.25);
      }

      h1 {
        margin-top: 0;
        font-size: 1.5rem;
        letter-spacing: -0.03em;
      }

      p.subtitle {
        margin-top: 0.2rem;
        font-size: 0.9rem;
        color: #6b7280;
      }

      form { margin-top: 1.3rem; }

      label {
        font-weight: 600;
        font-size: 0.85rem;
        display: block;
        margin-top: 0.8rem;
        margin-bottom: 0.25rem;
      }

      input[type="text"], select {
        padding: 0.45rem 0.6rem;
        width: 100%;
        border-radius: 0.6rem;
        border: 1px solid #e5e7eb;
        font-size: 0.9rem;
      }

      input[type="text"]:focus, select:focus {
        outline: none;
        border-color: #2563eb;
        box-shadow: 0 0 0 1px #bfdbfe;
      }

      .buttons {
        margin-top: 1.3rem;
        display: flex;
        gap: 0.6rem;
      }

      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.95rem;
        border-radius: 999px;
        border: 1px solid transparent;
        font-size: 0.9rem;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
        transition: background 120ms ease, color 120ms ease,
                    transform 80ms ease, box-shadow 80ms ease;
        white-space: nowrap;
      }

      .btn-primary {
        background: radial-gradient(circle at top left, #dbeafe, #2563eb);
        color: #ffffff;
      }

      .btn-primary:hover {
        background: radial-gradient(circle at top left, #bfdbfe, #1d4ed8);
      }

      .btn-secondary {
        background: rgba(255, 255, 255, 0.85);
        border-color: #d1d5db;
        color: #111827;
      }

      .btn-secondary:hover { background: #f9fafb; }

      a.btn { text-decoration: none; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <h1>Add new employee</h1>
        <p class="subtitle">Nieuwe medewerkers worden automatisch ge-onboard via het automation-script.</p>

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

          <div class="buttons">
            <button type="submit" class="btn btn-primary">Create &amp; start onboarding</button>
            <a href="{{ url_for('index') }}" class="btn btn-secondary">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  </body>
</html>
"""

LIST_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Employees - Innovatech HR Portal</title>
    <style>
      body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        padding: 0;
        background: radial-gradient(circle at top, #e0f2fe 0, #f9fafb 45%, #eef2ff 100%);
      }

      .container {
        max-width: 980px;
        margin: 2.2rem auto;
        padding: 0 1.5rem;
      }

      .card {
        background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(239,246,255,0.98));
        border-radius: 1rem;
        padding: 1.5rem 1.7rem 1.7rem;
        box-shadow:
          0 10px 25px rgba(15, 23, 42, 0.08),
          0 0 0 1px rgba(148, 163, 184, 0.25);
      }

      .header-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.9rem;
      }

      h1 {
        margin: 0;
        font-size: 1.5rem;
        letter-spacing: -0.03em;
      }

      p.subtitle {
        margin: 0.3rem 0 0;
        font-size: 0.88rem;
        color: #6b7280;
      }

      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.4rem 0.9rem;
        border-radius: 999px;
        border: 1px solid #d1d5db;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
        background: rgba(255,255,255,0.9);
        color: #111827;
      }

      .btn:hover { background: #f9fafb; }

      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 0.6rem;
        font-size: 0.86rem;
      }

      th, td {
        padding: 0.5rem 0.4rem;
        border-bottom: 1px solid #e5e7eb;
        text-align: left;
      }

      th {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6b7280;
      }

      tr:last-child td { border-bottom: none; }

      .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }

      .status-new      { background: #eff6ff; color: #1d4ed8; }
      .status-active   { background: #ecfdf5; color: #047857; }
      .status-inactive { background: #fef2f2; color: #b91c1c; }

      .badge-deprov-true {
        background: #dcfce7;
        color: #166534;
        border-radius: 999px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
      }

      .badge-deprov-false {
        background: #fee2e2;
        color: #b91c1c;
        border-radius: 999px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
      }

      .email-link {
        color: #2563eb;
        text-decoration: none;
      }

      .email-link:hover { text-decoration: underline; }

      .empty {
        margin-top: 0.5rem;
        font-size: 0.88rem;
        color: #6b7280;
      }

      .last-action {
        max-width: 18rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <div class="header-row">
          <div>
            <h1>Employees</h1>
            <p class="subtitle">Overzicht van alle medewerkers in de HR-database.</p>
          </div>
          <a href="{{ url_for('index') }}" class="btn">← Back to portal</a>
        </div>

        {% if employees %}
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Department</th>
                <th>Role</th>
                <th>Status</th>
                <th>Deprovisioned</th>
                <th>Last action</th>
              </tr>
            </thead>
            <tbody>
              {% for emp in employees %}
                <tr>
                  <td>{{ emp.id }}</td>
                  <td>{{ emp.name }}</td>
                  <td>
                    <a href="{{ url_for('index', email=emp.email) }}" class="email-link">{{ emp.email }}</a>
                  </td>
                  <td>{{ emp.department }}</td>
                  <td>{{ emp.role }}</td>
                  <td>
                    <span class="status-pill status-{{ emp.status|lower }}">{{ emp.status }}</span>
                  </td>
                  <td>
                    <span class="badge-deprov-{{ 'true' if emp.deprovisioned else 'false' }}">
                      {{ 'Yes' if emp.deprovisioned else 'No' }}
                    </span>
                  </td>
                  <td class="last-action">{{ emp.last_action or '-' }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <p class="empty">Er staan nog geen medewerkers in de database.</p>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""

# ---------- ROUTES ----------

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


@app.route("/employees", methods=["GET"])
def list_employees():
    """Overzicht met alle medewerkers."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, email, department, role, status,
                       deprovisioned, last_action
                FROM employees
                ORDER BY id;
                """
            )
            employees = cur.fetchall()
    finally:
        conn.close()

    return render_template_string(LIST_TEMPLATE, employees=employees)


@app.route("/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "GET":
        return render_template_string(ADD_TEMPLATE)

    # POST: form submit -> employee record & onboarding-script starten
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    department = request.form.get("department", "").strip()
    role = request.form.get("role", "").strip()

    if not name or not email or not department or not role:
        return render_template_string(ADD_TEMPLATE)

    # Deze worden (zoals in onboarding.py) uiteindelijk door automation ingevuld;
    # hier gebruiken we ze alleen voor logica/consistente helper-functies.
    workspace_username = generate_workspace_username(email)
    workspace_password = generate_temp_password()

    when = datetime.datetime.utcnow().isoformat() + "Z"
    action_text = f"Onboarding requested at {when}"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO employees (name, email, department, role, status, last_action)
                VALUES (%s, %s, %s, %s, 'NEW', %s);
                """,
                (name, email, department, role, action_text),
            )
        conn.commit()
    finally:
        conn.close()

    # onboarding.py automatisch starten (zoals voorheen)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    onboarding_script = os.path.join(project_root, "automation", "onboarding.py")
    subprocess.Popen(["python", onboarding_script])

    print(f"[PORTAL] Created NEW employee {email}, onboarding.py started")

    # Terug naar detailpagina
    return redirect(url_for("index", email=email))


@app.route("/offboard/<int:employee_id>", methods=["POST"])
def offboard_employee(employee_id: int):
    """
    Markeer employee als INACTIVE en start offboarding.py.

    offboarding.py zelf zorgt ervoor dat alleen status = INACTIVE
    én deprovisioned = FALSE verder verwerkt worden. :contentReference[oaicite:2]{index=2}
    """
    conn = get_db_connection()
    email = None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT email FROM employees WHERE id = %s;", (employee_id,))
            row = cur.fetchone()
            if not row:
                return redirect(url_for("index"))
            email = row["email"]

        when = datetime.datetime.utcnow().isoformat() + "Z"
        action_text = f"Marked INACTIVE from portal at {when}"

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE employees
                SET status = 'INACTIVE',
                    last_action = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (action_text, employee_id),
            )
        conn.commit()
    finally:
        conn.close()

    # offboarding-script starten
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    offboarding_script = os.path.join(project_root, "automation", "offboarding.py")
    subprocess.Popen(["python", offboarding_script])

    print(f"[PORTAL] Marked employee {email} (ID {employee_id}) INACTIVE, offboarding.py started")

    return redirect(url_for("index", email=email))


if __name__ == "__main__":
    # Dev-run: in Cloud Shell / lokaal
    app.run(host="0.0.0.0", port=8080, debug=True)
