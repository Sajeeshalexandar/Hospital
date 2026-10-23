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

This creates 2 hospitals, subscription plans, departments, and 4 ready-to-use user accounts:

| Role | Email | Password |
|---|---|---|
| Super Admin | `superadmin@medisaas.com` | `SuperAdminPass@123` |
| Hospital Admin | `apollo.admin@medisaas.com` | `AdminPass@123` |
| Doctor | `dr.ramesh@apollo.com` | `DoctorPass@123` |
| Receptionist | `priya.reception@apollo.com` | `StaffPass@123` |

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

## 🔒 Environment Variables (Production)

For production deployment, move these settings out of `config/settings.py` into environment variables:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@host/db
```

---

## 👨‍💻 Development Notes

- **Database**: SQLite (development). Switch to PostgreSQL for production.
- **Media files**: Stored in `media/` locally. Use S3 or similar for production.
- **Static files**: Run `python manage.py collectstatic` for production.

---

## 📄 License

MIT License — feel free to use and adapt for your own projects.

---

*Built by Sajee — MediSaaS Hospital Management SaaS*
