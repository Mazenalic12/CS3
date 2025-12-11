#!/usr/bin/env python3
"""
Onboarding Automation Service

Flow per nieuwe medewerker:
- Zoek employees met status = 'NEW' en cloud_account_created = false
- Maak een workspace-username + tijdelijk wachtwoord
- Maak een Windows VM in Compute Engine voor deze medewerker
- Maak op die VM een lokale Windows gebruiker met dat wachtwoord (startup script)
- Stuur een welkomstmail met alle gegevens
- Update de employees tabel:
    status = 'ACTIVE'
    cloud_account_created = true
    device_enrolled = true
    workspace_username, workspace_temp_password invullen
    last_action = 'Onboarding completed at ...'
"""

import os
import sys
import time
import datetime
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor

# ---- NIEUW: Google Compute Engine API ----
from googleapiclient import discovery
from googleapiclient.errors import HttpError

# ---- NIEUW: email versturen ----
import smtplib
from email.message import EmailMessage

# ========= CONFIG =========

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hr_employees")
DB_USER = os.getenv("DB_USER", "hr_app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")

# GCP project + zone voor de Windows VM's
GCP_PROJECT = os.getenv("GCP_PROJECT", "cs3-innovatech-hr-project")  # <-- jouw project ID
GCP_ZONE = os.getenv("GCP_ZONE", "europe-west1-b")
GCP_REGION = "europe-west1"  # hoort bij europe-west1-b

# Windows image (standaard Windows Server 2019)
WINDOWS_IMAGE_PROJECT = "windows-cloud"
WINDOWS_IMAGE_FAMILY = "windows-2019"

NETWORK = f"projects/{GCP_PROJECT}/global/networks/innovatech-vpc"
SUBNETWORK = f"projects/{GCP_PROJECT}/regions/{GCP_REGION}/subnetworks/automation"

# SMTP voor welkomstmail  (Gmail voorbeeld)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("HR_SMTP_USER")       # <-- zet deze als env var
SMTP_PASSWORD = os.getenv("HR_SMTP_PASS")   # <-- zet deze als env var

# ================= HELPERS =================

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    return conn


def generate_temp_password(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_username(emp):
    """Maak een simpele username, bv. voornaam.achternaam of fallback."""
    name = emp["name"].strip().lower()
    safe = "".join(c for c in name.replace(" ", ".") if c.isalnum() or c == ".")
    if not safe:
        safe = f"user{emp['id']}"
    return safe[:20]


# ========= GOOGLE COMPUTE ENGINE ==========

_compute_client = None


def get_compute_client():
    global _compute_client
    if _compute_client is None:
        _compute_client = discovery.build("compute", "v1", cache_discovery=False)
    return _compute_client


def wait_for_operation(compute, project, zone, op_name):
    """Wacht tot de instance-create operation klaar is."""
    while True:
        result = compute.zoneOperations().get(
            project=project, zone=zone, operation=op_name
        ).execute()

        if result.get("status") == "DONE":
            if "error" in result:
                raise RuntimeError(f"GCE operation error: {result['error']}")
            return
        time.sleep(5)


def create_windows_vm_for_employee(emp, username, temp_password):
    """
    Maakt een Windows VM + lokale user met RDP-rechten.
    Retourneert (instance_name, public_ip).
    """
    compute = get_compute_client()

    instance_name = f"hr-ws-{emp['id']}"
    instance_name = instance_name.replace("_", "-")

    # Haal de laatste image uit de windows-2019 familie
    image_response = compute.images().getFromFamily(
        project=WINDOWS_IMAGE_PROJECT,
        family=WINDOWS_IMAGE_FAMILY,
    ).execute()
    source_disk_image = image_response["selfLink"]

    # Startup script: maakt lokale user aan op Windows
    startup_script = f"""
<powershell>
$u = "{username}"
$p = "{temp_password}"
net user $u $p /add
net localgroup "Remote Desktop Users" $u /add
</powershell>
"""

    config = {
        "name": instance_name,
        "machineType": f"zones/{GCP_ZONE}/machineTypes/e2-standard-2",
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": source_disk_image,
                    "diskSizeGb": "50",
                },
            }
        ],
        "networkInterfaces": [
            {
                # jouw VPC:
                "network": f"projects/{GCP_PROJECT}/global/networks/innovatech-vpc",
                # jouw subnet in europe-west1:
                "subnetwork": f"projects/{GCP_PROJECT}/regions/europe-west1/subnetworks/innovatech-vpc-automation",
                "accessConfigs": [
                    {
                        "type": "ONE_TO_ONE_NAT",
                        "name": "External NAT",
                    }
                ],
            }
        ],


        "metadata": {
            "items": [
                {
                    "key": "windows-startup-script-ps1",
                    "value": startup_script,
                }
            ]
        },
        "tags": {"items": ["allow-rdp"]},
    }

    print(f"[VM] Creating Windows VM {instance_name} in {GCP_ZONE}...")

    op = compute.instances().insert(
        project=GCP_PROJECT, zone=GCP_ZONE, body=config
    ).execute()

    wait_for_operation(compute, GCP_PROJECT, GCP_ZONE, op["name"])

    # VM info ophalen om public IP te tonen
    inst = compute.instances().get(
        project=GCP_PROJECT, zone=GCP_ZONE, instance=instance_name
    ).execute()

    nic = inst["networkInterfaces"][0]
    access_cfg = nic.get("accessConfigs", [])[0]
    public_ip = access_cfg.get("natIP")

    print(f"[VM] VM ready: {instance_name} (IP: {public_ip})")
    return instance_name, public_ip


# ========== EMAIL ==========

def send_welcome_email(emp, username, temp_password, public_ip):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[MAIL] SMTP env vars niet gezet, email wordt overgeslagen.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Welkom bij Innovatech – je account en werkplek zijn aangemaakt"
    msg["From"] = SMTP_USER
    msg["To"] = emp["email"]

    body = f"""Hallo {emp['name']},

Welkom bij Innovatech! Je account en virtuele werkplek zijn aangemaakt.

Afdeling: {emp.get('department') or '-'}
Rol (HR): {emp.get('role') or '-'}

Windows werkplek (GCP VM)
-------------------------
VM public IP: {public_ip}
Gebruikersnaam: {username}
Tijdelijk wachtwoord (eerste login): {temp_password}

Je kunt inloggen via Remote Desktop (RDP) vanaf je eigen pc/laptop.
Bij de eerste login moet je je wachtwoord direct wijzigen.

Je ontvangt deze mail automatisch vanuit het HR self-service portal.

Met vriendelijke groet,
Innovatech HR
"""
    msg.set_content(body)

    print(f"[MAIL] Sending welcome email to {emp['email']}...")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    print("[MAIL] Email sent.")


# ========== DATABASE LOGIC ==========

def fetch_new_employees(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT *
            FROM employees
            WHERE status = 'NEW'
              AND cloud_account_created = false
            ORDER BY id;
            """
        )
        return cur.fetchall()


def mark_employee_as_onboarded(conn, emp_id, username, temp_password):
    now = datetime.datetime.utcnow().isoformat() + "Z"
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE employees
            SET
                status = 'ACTIVE',
                cloud_account_created = true,
                device_enrolled = true,
                workspace_username = %s,
                workspace_temp_password = %s,
                last_action = %s,
                updated_at = NOW()
            WHERE id = %s;
            """,
            (username, temp_password, f"Onboarding completed at {now}", emp_id),
        )
    conn.commit()


# ========== MAIN FLOW ==========

def main():
    print("=== Onboarding run started ===")
    conn = get_db_connection()
    try:
        employees = fetch_new_employees(conn)
        if not employees:
            print("No employees to onboard.")
            return

        print(f"Found {len(employees)} employee(s) to onboard.")

        for emp in employees:
            print(f"\nProcessing employee ID {emp['id']} - {emp['email']}")

            username = generate_username(emp)
            temp_password = generate_temp_password()

            try:
                instance_name, public_ip = create_windows_vm_for_employee(
                    emp, username, temp_password
                )
            except HttpError as e:
                print(f"[ERROR] Failed to create VM for {emp['email']}: {e}")
                continue

            # Welkomstmail
            send_welcome_email(emp, username, temp_password, public_ip)

            # DB updaten
            mark_employee_as_onboarded(conn, emp["id"], username, temp_password)
            print("[OK] Employee marked as ACTIVE in database.")

        print("\n=== Onboarding run finished successfully ===")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
