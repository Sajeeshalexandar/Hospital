# 🏥 MediSaaS — Hospital Management SaaS

A multi-tenant Hospital Management System built with Django.  
Supports 4 roles across multiple hospitals on a single platform.

---

## ✨ Features

| Module | Description |
|---|---|
| **Super Admin** | Manage hospitals, subscription plans, global audit trail |
| **Hospital Admin** | Staff, departments, settings, billing overview |
| **Doctor** | Queue, consultations, prescriptions, lab orders |
| **Receptionist** | Patient registration, appointments, billing (cashier) |
| **Laboratory** | Test orders, report upload & review |
| **Billing** | Invoice generation, payment recording, receipts |
| **Notifications** | In-app alerts for appointments, prescriptions, lab results |
| **Audit Logs** | Immutable backend-only audit trail (Rule #11) |

---

## 🛠️ Prerequisites

- Python **3.12+** (tested on 3.14)
- `pip`
- Windows / Linux / macOS
- Git

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Sajeeshalexandar/hospital-management-saas.git
cd hospital-management-saas
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Seed the demo dataset

```bash
python manage.py seed_demo_data
```

This creates 2 hospitals, subscription plans, departments, and ready-to-use accounts for each portal:

| Role | Email | Password |
|---|---|---|
| Super Admin | `superadmin@medisaas.com` | `SuperAdminPass@123` |
| Hospital Admin | `apollo.admin@medisaas.com` | `AdminPass@123` |
| Doctor | `dr.ramesh@apollo.com` | `DoctorPass@123` |
| Receptionist | `priya.reception@apollo.com` | `StaffPass@123` |
| Hospital Staff | `staff.demo@apollo.com` | `StaffPass@123` |
| Patient | `anil.kapoor@example.com` | `PatientPass@123` |

> The seed command is **idempotent** — running it multiple times is safe (uses `get_or_create`).

### 6. Run the development server

```bash
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000/**

---

## 🧪 Running Tests

```bash
python manage.py test --verbosity=2
```

Expected output: `Ran 6 tests — OK`

Tests cover:
- **Rule #8** — Appointment conflict prevention (no double-booking a doctor)
- **Rule #9** — Server-side billing arithmetic (subtotal, tax, discount, totals)
- Invoice number generation, payment status transitions
- Lab report number generation, workflow transitions

---

## 🗂️ Project Structure

```
Hospital/
├── accounts/           # Custom User model, authentication, roles
│   └── management/
│       └── commands/
│           └── seed_demo_data.py
├── appointments/       # Appointment booking with conflict prevention
├── audit_logs/         # Immutable audit trail
├── billing/            # Invoices, items, payments
├── config/             # Django settings, root URLs
├── dashboards/         # Role-specific dashboards
├── departments/        # Hospital departments
├── doctors/            # Doctor profiles, availability
├── hospitals/          # Hospital tenants, settings
├── laboratory/         # Lab test orders and reports
├── medical_records/    # Diagnosis, treatment notes
├── memberships/        # Hospital-user memberships
├── notifications/      # In-app notification system
├── patients/           # Patient registration and profiles
├── prescriptions/      # Prescriptions and medication
├── staff/              # Receptionist / non-doctor staff profiles
├── subscriptions/      # Subscription plans and hospital subscriptions
├── templates/          # All HTML templates (role-separated)
├── static/             # CSS, JS, images
├── media/              # Uploaded files (lab reports, etc.)
├── requirements.txt
└── manage.py
```

---

## 🏗️ Architecture Highlights

### Multi-Tenant Isolation
Every queryset is scoped to the logged-in user's hospital via `get_user_hospital(request.user)`. No cross-hospital data leakage is possible.

### Role-Based Access (4 roles)
| Role | Django Group | Redirect After Login |
|---|---|---|
| `SUPER_ADMIN` | — | `/super-admin/dashboard/` |
| `HOSPITAL_ADMIN` | — | `/hospital-admin/dashboard/` |
| `DOCTOR` | — | `/doctor/dashboard/` |
| `RECEPTIONIST` | — | `/receptionist/dashboard/` |

### Critical Business Rules
- **Rule #8** — Appointment conflict check: a doctor cannot have two overlapping appointments
- **Rule #9** — All billing totals are computed server-side only (`_recalculate_invoice`), never via client-side JS
- **Rule #11** — Audit logs are written from backend views only, never from the browser

---

## 📦 Dependencies

Key packages (see `requirements.txt` for full list):

| Package | Purpose |
|---|---|
| Django | Web framework |
| Pillow | Image handling (profile photos, lab uploads) |
| django-crispy-forms | Form rendering with Bootstrap 5 |
| crispy-bootstrap5 | Bootstrap 5 template pack |

---

## 🔒 Deploying to Render

The included `render.yaml` defines a Python web service that connects to your existing Render PostgreSQL database. It does not create another database. Push the repository to GitHub, choose **New → Blueprint** in Render, connect the repository, and apply the Blueprint.

| Render setting | Value |
|---|---|
| Web service name | `hospital-management-saas` |
| Runtime | Python |
| Region | Ohio (`ohio`) — match the database region |
| Build command | `bash website/build.sh` |
| Start command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT` |
| Web service plan | Free (demo/testing) |
| PostgreSQL | Use the existing database; this Blueprint does not provision one |
| Database name | `hospital_management_m4kd` |
| Database user | `hospital_management_m4kd_user` |
| PostgreSQL version | 18 |
| Database port | 5432 |

Set these web-service environment variables:

| Variable | Value |
|---|---|
| `SECRET_KEY` | Generated by Render; keep it secret |
| `DEBUG` | `False` |
| `DATABASE_URL` | The database's **Internal Database URL** from Render's Connect menu; entered as a secret |
| `RENDER_EXTERNAL_HOSTNAME` | Set automatically by Render |

The database URL contains the hostname, port, database name, username, and password. Copy the full **Internal Database URL** from the database's Connect menu; do not construct it from the host shown in the database overview, and do not add the password separately. The listed host may be the external host. Use the internal URL because the web service and database are both in Ohio. The rotated password must be reflected in the internal URL.

For a manual service, choose **Web Service**, Python runtime, Ohio region, and the same build/start commands above. Set `DATABASE_URL`, `DEBUG=False`, and `SECRET_KEY` in the service's Environment page. For a custom domain, set `ALLOWED_HOSTS` to comma-separated hostnames and `CSRF_TRUSTED_ORIGINS` to comma-separated full origins such as `https://hospital.example.com`.

The build command collects static files and applies migrations. Your existing database already contains the imported SQLite records, so do **not** run the transfer script again or seed demo data into it.

### Transfer the existing SQLite records

If you still need to transfer data to a new, empty PostgreSQL database, make a secure backup of `db.sqlite3`, deploy the service, and do not seed or otherwise add records to the target before importing. Activate the project virtual environment in PowerShell and run:

```powershell
.\scripts\transfer_sqlite_to_render.ps1
```

The script exports the local SQLite data with Django fixtures, preserving application primary keys and relationships. It prompts for the database's **External Database URL** with hidden input, verifies the destination is PostgreSQL and has no application records, applies migrations, and imports the fixture. The external URL is used only in the local process; do not paste it into source files, `render.yaml`, or chat. The script removes its temporary export after a successful import; if it fails, the export stays in the ignored `.local-data-transfer/` folder for a controlled retry. The import is intended to run once against an empty database.

The export transfers database records only. Uploaded images and lab reports live under `media/` and must be moved to configured object storage separately. Do not import real patient data into a free/demo service; confirm applicable privacy, security, and backup requirements first.

---

## 👨‍💻 Development Notes

- **Database**: SQLite (development). Switch to PostgreSQL for production.
- **Media files**: Hospital template images and lab reports are stored in `media/` locally. Render's service filesystem is ephemeral; configure S3 or compatible object storage before relying on uploaded files in production.
- **Static files**: Run `python manage.py collectstatic` for production.
- **Render free plan**: Free PostgreSQL databases expire after their current free-plan period. Back up data or select a suitable paid database for long-term use.
- **Patient data**: Do not store real patient/medical records on a free demo deployment. Verify applicable privacy, security, and backup requirements before using real data.
- **Database networking**: After local import, remove or restrict the database's `0.0.0.0/0` external inbound rule if no external clients need access. Same-region Render services can continue using the internal URL.

---

## 📄 License

MIT License — feel free to use and adapt for your own projects.

---

*Built by Sajee — MediSaaS Hospital Management SaaS*
