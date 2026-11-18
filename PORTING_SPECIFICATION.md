# MediSaaS Hospital Management System: Porting Specification

## 1. Purpose and scope

This document describes the application as it is implemented in this repository. It is intended as a functional and data-model handoff for rebuilding the product in another language or framework. It includes current behavior and calls out places where the code, README, and apparent product intent do not fully agree.

The application is a server-rendered Django hospital-management SaaS. It has a public hospital/doctor website, staff and patient portals, clinical workflows, billing, and platform-level hospital/subscription administration. The source project uses Django templates rather than a separate frontend/API client.

## 2. Architecture and runtime

- **Web framework:** Django 6.1.2, Python 3.12+ according to the README.
- **Database in this checkout:** SQLite (`db.sqlite3`). The README suggests PostgreSQL for production.
- **Authentication:** Django session authentication using a custom `accounts.User`. Users submit email and password; login code attempts authentication using email/username.
- **Frontend:** Django HTML templates, Bootstrap 5.3.3 and Bootstrap Icons loaded from CDNs, plus static CSS/JavaScript.
- **Uploads:** Django media storage; lab report attachments use `lab_reports/`, and hospital template preview images use `templates/`.
- **Timezone:** `USE_TZ=True`, configured timezone is UTC. Hospital settings also store a per-hospital timezone, but application workflows commonly use Django's configured timezone.
- **Applications/modules:** `accounts`, `hospitals`, `memberships`, `subscriptions`, `departments`, `doctors`, `patients`, `staff`, `appointments`, `medical_records`, `prescriptions`, `laboratory`, `billing`, `notifications`, `dashboards`, `audit_logs`, and `website`.
- `patient_portal` exists as a Django package but is not in `INSTALLED_APPS`; its models file is empty and it is not the active portal implementation. The active public portal routes are in `website`.
- There is no separate REST API, payment-gateway integration, email/SMS delivery integration, or pharmacy inventory module in the current implementation.

## 3. Roles and access control

The implemented application has **six role types**, although the README's role table describes only four.

| Role | How identified | Main capabilities |
|---|---|---|
| Super Admin | Django `is_superuser=True` | Platform-wide hospital and subscription management, global analytics and audit visibility |
| Hospital Admin | Active `HospitalMembership.role=HOSPITAL_ADMIN` | Manage own hospital, departments, staff/doctors, hospital settings; access operational modules and analytics |
| Doctor | Active membership role `DOCTOR` | View/manage clinical appointments, patient records, prescriptions, lab orders, and own availability |
| Receptionist | Active membership role `RECEPTIONIST` | Front-desk appointment and patient workflows; access selected billing/lab/clinical views |
| Staff | Active membership role `STAFF` | Selected hospital operational, lab, billing, and dashboard functions |
| Patient | An active `PatientProfile` linked to the account | View own dashboard and update contact details; public online appointment booking is also available |

### Role resolution and permissions

1. A superuser is treated as Super Admin.
2. A user with an active patient profile is treated as a Patient by login/dispatch logic.
3. Other staff users are assigned a role by an active hospital membership.
4. Role decorators protect server-side views; the role is not meant to be trusted from a submitted form.
5. Hospital staff views obtain the user's hospital from the database, then filter records by that hospital. Object detail/edit endpoints normally scope the requested object to that hospital.
6. Patient dashboard data is filtered by the logged-in user's patient profile.
7. Patient records do not use `HospitalMembership`; they are linked through `PatientProfile.user`.

The data model permits a user to have memberships in multiple hospitals (unique per user/hospital), but the shared helper fetches a single active membership and treats multiple active memberships as an error/no membership. A port should decide whether a user may work across tenants and model role selection accordingly.

### Practical permission matrix

Permissions vary by individual endpoint, not just by dashboard:

| Area | Super Admin | Hospital Admin | Doctor | Receptionist | Staff | Patient |
|---|---:|---:|---:|---:|---:|---:|
| Hospital/plan/subscription administration | Yes | No | No | No | No | No |
| Department, staff, doctor administration | No | Yes | No | No | No | No |
| Appointment list/create/status | No | Yes | Yes | Yes | No | Public booking only |
| Patient list/detail | No | Yes | Yes | Yes | No | Own dashboard only |
| Patient create/edit | No | Yes | No | Yes | No | Own contact fields only |
| Clinical records | No | Yes | Yes | Read/list/detail | No | Own dashboard |
| Prescriptions | No | Yes | Yes | Read/list/detail | No | Own dashboard |
| Laboratory | No | Yes | Yes | Create/read | Yes, selected workflows | Own dashboard |
| Billing | No | Yes | Yes, read/list/detail | Yes | Yes | Own dashboard |
| Audit log | Not through normal role decorator | Yes, own hospital | No | No | No | No |

This is a summary. For a faithful port, reproduce endpoint-specific permissions rather than relying solely on this table.

## 4. Database design

IDs below are Django primary keys. `created_at`/`updated_at` fields are included where described; use database-generated timestamps or application-managed timestamps with equivalent behavior. Decimal money fields should remain fixed precision, not binary floating point.

### Accounts and tenant setup

| Entity | Important fields and relationships |
|---|---|
| **User** (`accounts.User`) | Extends Django's user with unique `email`; retains username, names, password hash, active/staff/superuser flags and Django authentication fields. |
| **HospitalTemplate** | `name` (unique), `template_code` (unique), description, optional preview image, active flag, timestamps. One template may be selected by many hospitals. |
| **Hospital** | Name, unique registration number, unique email, phone/address/city/state/country/postal code, optional template FK, status (`ACTIVE`, `INACTIVE`, `SUSPENDED`), timestamps. |
| **HospitalSettings** | One-to-one hospital; timezone, currency (default INR), appointment duration (default 30 minutes), allow-online-appointments flag, timestamps. |
| **HospitalMembership** | User FK, hospital FK, role (`HOSPITAL_ADMIN`, `DOCTOR`, `RECEPTIONIST`, `STAFF`), active flag, joined/created/updated timestamps. Unique constraint on `(user, hospital)`. |
| **SubscriptionPlan** | Name, unique code, decimal price, currency, duration in days, maximum users/patients, JSON features, active flag, timestamps. |
| **HospitalSubscription** | Hospital FK and plan FK, status (`TRIAL`, `ACTIVE`, `EXPIRED`, `CANCELLED`, `SUSPENDED`), start/end timestamps, auto-renew flag, optional cancelled time, timestamps. |
| **Department** | Hospital FK, name, optional description, active flag, timestamps. Unique `(hospital, name)`; ordered by name. |

### People and schedules

| Entity | Important fields and relationships |
|---|---|
| **DoctorProfile** | User FK, hospital FK, department FK, employee code, qualification, specialization, experience years, consultation fee, OP commission percentage, contact number, active flag, timestamps. Employee code unique within hospital. |
| **DoctorAvailability** | Doctor FK, weekday (0 Monday through 6 Sunday), start/end time, optional effective date range, active flag, created time. Validation requires end after start and effective-until not before effective-from. |
| **PatientProfile** | Optional user FK, hospital FK, patient ID code, DOB, gender, phone, address, blood group, emergency contact name/phone, active flag, timestamps. Patient ID unique within hospital. DOB cannot be in the future. |
| **StaffProfile** | User FK, hospital FK, employee code, job title, contact number, joining date, active flag, timestamps. Employee code unique within hospital. Receptionist and general Staff memberships both use this profile. |

### Clinical and operational records

| Entity | Important fields and relationships |
|---|---|
| **Appointment** | Hospital, patient, doctor, department FKs; start/end datetimes; reason; status (`PENDING`, `CONFIRMED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`); cancellation reason; optional created-by user; timestamps. End must be after start. Ordered by start time. |
| **MedicalRecord** | Hospital, patient, doctor, appointment, and created-by FKs; symptoms, diagnosis, treatment notes, optional follow-up date, timestamps. Ordered newest first. |
| **Prescription** | Hospital, appointment, patient, and doctor FKs; prescription number unique within hospital; status (`DRAFT`, `ISSUED`, `CANCELLED`); notes; optional issue time; timestamps. |
| **PrescriptionMedicine** | Prescription FK; medicine name, strength, dosage, route, frequency, duration, optional decimal quantity, instructions. Medicine details are text fields, not linked to a drug catalogue. |
| **LabTestOrder** | Hospital, patient, doctor FKs; optional appointment FK; test name, clinical notes, status (`REQUESTED`, `COLLECTED`, `PROCESSING`, `COMPLETED`, `CANCELLED`); ordered/updated timestamps. |
| **LabReport** | Order, hospital, patient FKs; report number unique within hospital; result summary, optional uploaded file, remarks, optional verified-by user, tested/reported timestamps, created time. |

### Finance, communication, and audit

| Entity | Important fields and relationships |
|---|---|
| **Invoice** | Hospital and patient FKs; optional appointment FK; invoice number unique within hospital; issue time, optional due date; subtotal, discount, tax, total as decimals; status (`DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `VOID`, `OVERDUE`); notes and timestamps. |
| **InvoiceItem** | Invoice FK; description, type (`CONSULTATION`, `LABORATORY`, `PROCEDURE`, `MEDICINE`, `OTHER`), decimal quantity/unit price/discount/tax/line total. |
| **Payment** | Invoice FK; amount, method (`CASH`, `CARD`, `BANK_TRANSFER`, `ONLINE`, `OTHER`), status (`PENDING`, `COMPLETED`, `FAILED`, `REFUNDED`), optional transaction reference/paid time/received-by user/notes, created time. |
| **Notification** | User FK, optional hospital FK, type, title, message, read flag, optional read time, created time. Ordered newest first. |
| **AuditLog** | Optional hospital and actor FKs; action, entity type/id, description, optional IP address, created time. Ordered newest first. |

### Main relationship map

```text
User ──< HospitalMembership >── Hospital ──< Department
  │                                  │           │
  ├──< PatientProfile >──────────────┤           └──< DoctorProfile >── User
  ├──< DoctorProfile                 ├──< StaffProfile >────────────── User
  ├──< StaffProfile                  ├──< Appointment >── PatientProfile
  └──< Notification                  │        │  └─────── DoctorProfile
                                     │        ├── MedicalRecord
                                     │        ├── Prescription ──< PrescriptionMedicine
                                     │        ├── LabTestOrder ───< LabReport
                                     │        └── Invoice ────────< InvoiceItem
                                     │                        └──< Payment
                                     ├──< HospitalSubscription >── SubscriptionPlan
                                     └──< AuditLog
```

The same hospital is redundantly stored on appointments, clinical records, lab records, invoices, and other tenant-owned rows. This makes tenant scoping explicit, but the current model declarations do not enforce every cross-table invariant (for example, that an appointment's doctor, patient, and department all belong to its hospital). Forms scope selectable records in common workflows; a port should also enforce these invariants server-side and/or with database constraints.

## 5. Workflows and business logic

### A. Public website and online booking

1. `/` displays active hospitals, active departments, and up to eight active doctors ordered by experience. It also shows system-wide summary values.
2. `/find-doctors/` supports filtering by department and hospital and searching name/specialization.
3. `/services/` lists active departments.
4. `/book-appointment/` accepts hospital, doctor, patient name, phone, optional email, gender, date/time, and reason.
5. The selected doctor must belong to the selected hospital. The department is taken from the doctor, rather than trusted from the posted department value.
6. The booking time is parsed and made timezone-aware; duration is hard-coded to 30 minutes. Past times are rejected.
7. A conflict is any existing `PENDING` or `CONFIRMED` appointment for that doctor where `existing.start < requested.end` and `existing.end > requested.start`. Overlap returns an error.
8. Patient lookup is by selected hospital and phone. If not found, create a patient profile, generated patient code, and associated user (email or synthetic email). The online-booking path assigns a placeholder DOB approximately 25 years before today and an online-registration address.
9. Create a `PENDING` appointment and notify the doctor in-app. Render a booking-success page.

Internal booking uses `/appointments/book/` and selects active patients, doctors, and departments in the current hospital. It uses the same overlap rule through form validation, records `created_by`, writes an audit event, notifies the doctor, and opens the appointment detail page.

### B. Staff appointment and consultation workflow

1. Front desk/admin/doctor browses hospital appointments with optional status, doctor, date, and patient/reason search. A doctor sees their own appointments by default.
2. Authorized user creates appointment; initial status is `PENDING`.
3. Appointment status can be updated. Cancellation requires a cancellation reason.
4. Doctor/admin creates a medical record from the appointment with symptoms, diagnosis, treatment notes, and optional follow-up date. Creating the record marks the appointment `COMPLETED`.
5. Doctor/admin can create a prescription linked to the appointment. It starts as `DRAFT`.
6. Medicines are added or removed while draft. Doctor/admin can issue or cancel it; issue time is recorded and the patient receives an in-app notification if linked to a user.
7. A lab order may be attached to patient/doctor and optionally an appointment. It starts `REQUESTED`; selected roles advance status. Uploading a report creates a generated report number if absent, associates it with the patient/order, marks the order `COMPLETED`, logs the upload, and notifies the doctor.

### C. Patient self-service

- Patient login is a dedicated `/login/patient/` page. Successful patient access requires an active `PatientProfile` linked to the account.
- `/patient/dashboard/` shows the next upcoming pending/confirmed appointment, appointment history, doctors previously seen, medical records, prescriptions and their medicines, lab orders/reports, invoices/items/payments, and notifications.
- The patient can update contact number, address, and emergency contact fields from the dashboard.
- `/patient-portal/` is a separate **public lookup** page. It accepts a patient ID or phone number and displays a matching patient's latest appointments, prescriptions, and lab orders without requiring login. The lookup searches across hospitals and uses the first match. Treat this as a different, privacy-sensitive behavior from the authenticated patient dashboard when porting.

### D. Hospital administration

- Super Admin creates/edits/deactivates hospitals, creates templates, and assigns subscription plans. Hospital creation also creates default hospital settings.
- Hospital Admin sees their own hospital profile/settings and can update settings (timezone, currency, appointment duration, online booking flag), but not core hospital identity.
- Hospital Admin manages departments, doctors, and staff. Doctor/staff creation is atomic: create user, membership, and profile together. Staff form allows only Receptionist or Staff membership roles.
- Doctor schedules can be added/removed by Hospital Admin; doctors can view their own active availability.
- Hospital Admin dashboard shows counts, today's/upcoming appointments, pending/completed counts, financial totals, recent invoices/lab orders/prescriptions, subscription, and notifications.
- Hospital analytics computes appointment completion/cancellation, billing collection, department/doctor volumes, lab completion, patient/record/prescription counts, and a composite operational score.

### E. SaaS administration and subscriptions

- Super Admin dashboard includes hospital/user/patient/membership counts, recent hospitals/audits, subscription plans/subscriptions/templates, and notifications.
- Super Admin analytics aggregates global hospital/user/appointment/invoice/audit data and calculates MRR/ARR from active subscriptions.
- Subscription plan fields include price, billing duration, usage caps and JSON feature flags. Hospital subscriptions store status, dates, and auto-renew.
- Current views manage plan/subscription records but do not enforce plan user/patient caps, expire subscriptions automatically, or perform payment/renewal processing.

### F. Billing and payments

1. Staff/admin/receptionist creates a draft invoice for an active same-hospital patient; appointment is optional. Invoice number is generated as `INV-YYYY-NNNN` if blank.
2. Add items with quantity, unit price, discount, and tax. The server computes `line_total = max(0, quantity * unit_price - item_discount + item_tax)`.
3. Recalculation sets `subtotal = sum(quantity * unit_price)` and `total = max(0, sum(line_total) - invoice_discount + invoice_tax)`.
4. If there are items and no payment, a draft becomes issued. Completed payments determine `PARTIALLY_PAID` or `PAID`; void status is preserved. Balance due is clamped at zero.
5. Authorized staff record payment as `COMPLETED` immediately, set received-by and paid-at, recalculate invoice, log the action, and notify the patient if linked to a user.
6. Invoice list/detail supports status/search, summary totals, payments, balance, and a print view. No gateway is called; the application records payments entered by staff.

### G. Notifications and audit

- Notifications are in-app records shown in navigation and notification pages; users can mark one or all as read. Appointment creation, prescription issue, lab report upload, and payment recording create notifications in selected flows.
- Audit entries are created from backend views for selected important operations such as patient registration, appointments, diagnosis, prescriptions, lab reports, and billing. Hospital Admin sees their hospital's last 100 entries; Super Admin analytics can see global audit data.
- Audit logging is not attached to every model mutation. The helper catches database/logging exceptions and silently returns no audit record, so it is not a guaranteed immutable audit ledger.

## 6. Statuses and transition summary

| Record | Values | Common implemented transitions |
|---|---|---|
| Hospital | ACTIVE, INACTIVE, SUSPENDED | Edited by Super Admin |
| Membership/profile | active boolean | Admin activates/deactivates profile; membership is separately active |
| Appointment | PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW | New booking -> PENDING; manual status updates; medical-record creation -> COMPLETED |
| Prescription | DRAFT, ISSUED, CANCELLED | Create -> DRAFT; doctor/admin issues or cancels; medicines editable only while DRAFT |
| Lab order | REQUESTED, COLLECTED, PROCESSING, COMPLETED, CANCELLED | Create -> REQUESTED; allowed users update status; report upload -> COMPLETED |
| Invoice | DRAFT, ISSUED, PARTIALLY_PAID, PAID, VOID, OVERDUE | Create -> DRAFT; item/payment recalculation; staff may manually set status |
| Payment | PENDING, COMPLETED, FAILED, REFUNDED | Payment-entry view creates directly as COMPLETED; other states are model values |
| Subscription | TRIAL, ACTIVE, EXPIRED, CANCELLED, SUSPENDED | Super Admin edits records; no automatic lifecycle processor found |

## 7. Route map

Public pages:

- `/` landing page; `/book-appointment/`; `/patient-portal/`; `/find-doctors/`; `/services/`; `/portals/`.
- Role login pages: `/login/super-admin/`, `/login/hospital-admin/`, `/login/doctor/`, `/login/receptionist/`, `/login/staff/`, `/login/patient/`; `/login/` redirects to the portals gateway; `/logout/`.
- `/dashboard/` dispatches the authenticated user to the dashboard for the database-resolved role.

Role dashboards and tenant modules:

- Dashboards: `/super-admin/dashboard/`, `/super-admin/analytics/`, `/hospital-admin/dashboard/`, `/hospital-admin/analytics/`, `/doctor/dashboard/`, `/receptionist/dashboard/`, `/staff/dashboard/`, `/patient/dashboard/`.
- Hospital and subscription management: `/super-admin/hospitals/...`, `/super-admin/plans/...`, `/super-admin/subscriptions/...`.
- Hospital operations: `/hospital-admin/my-hospital/`, `/hospital-admin/my-hospital/settings/`, `/hospital-admin/departments/...`, `/hospital-admin/doctors/...`, `/hospital-admin/staff/...`; doctors also have `/doctor/my-availability/`.
- Patients: `/patients/`, `/patients/create/`, `/patients/<id>/`, `/patients/<id>/edit/`, `/patients/<id>/delete/`.
- Appointments: `/appointments/`, `/appointments/book/`, `/appointments/<id>/`, `/appointments/<id>/status/`.
- Clinical records: `/medical-records/`, `/medical-records/create/<appointment_id>/`, `/medical-records/<id>/`, `/medical-records/<id>/edit/`.
- Prescriptions: `/prescriptions/`, `/prescriptions/create/<appointment_id>/`, `/prescriptions/<id>/`, `/prescriptions/<id>/add-medicine/`, `/prescriptions/medicine/<id>/delete/`.
- Laboratory: `/laboratory/orders/`, `/laboratory/orders/create/`, `/laboratory/orders/<id>/status/`, `/laboratory/orders/<id>/report/`, `/laboratory/reports/<id>/`.
- Billing: `/billing/invoices/`, `/billing/invoices/create/`, `/billing/invoices/<id>/`, item add/delete, payment record, and invoice status endpoints under `/billing/invoices/...`.
- Notifications: `/notifications/`, `/notifications/<id>/read/`, `/notifications/read-all/`; audit: `/audit-logs/`.
- Custom Django admin sites are mounted at `/admin/super/`, `/admin/hospital/`, `/admin/doctor/`, `/admin/receptionist/`; Django's built-in admin is `/admin/`.

## 8. UI behavior

- Public landing pages promote hospital services and doctors; the doctor directory can be filtered/searched; the booking page is the unauthenticated conversion flow.
- Login pages are separate by role and have role-specific visual styling. The patient login screen uses email/password fields, CSRF-protected POST, Django message alerts, and a client-side password visibility toggle.
- Authenticated portals use a shared base layout and role-specific sidebars. The patient sidebar links dashboard sections and online booking; the doctor sidebar links appointment, record, prescription, lab, patient, and availability workspaces.
- Most CRUD screens are server-rendered forms and lists with Django messages for success/errors. Financial invoice detail includes print mode.
- Unread notification count is injected into template context.

## 9. Important implementation details and gaps to account for

These are observable behaviors to decide whether to preserve or improve during a port:

1. **Role documentation drift:** the README says four roles, while login configuration and dashboard routes implement six.
2. **Patient lookup privacy:** the unauthenticated portal exposes clinical-adjacent data using only patient ID/phone. Do not copy this lookup without an explicit privacy/authentication decision.
3. **Online-created patient account:** public booking creates/links a user but does not establish a patient password or send an account activation message. A patient may not be able to use patient login without a separate credential setup.
4. **Booking settings are not applied:** online booking duration is fixed at 30 minutes and does not consult `HospitalSettings.appointment_duration_minutes` or `allow_online_appointments`.
5. **Availability is informational:** appointment booking checks doctor overlap but does not verify the doctor has an active availability slot, that the selected department matches the doctor, or (for internal booking) that the time is in the future.
6. **Race condition risk:** appointment conflicts are checked in application logic before insert; there is no database-level exclusion/locking constraint to prevent two simultaneous requests from taking the same slot.
7. **Tenant invariants:** many forms scope choices by hospital, but model-level cross-tenant consistency is not uniformly enforced.
8. **Patient-account uniqueness:** `PatientProfile.user` is not unique. Some patient flows assume a single active profile for a user.
9. **Plan limits and subscription lifecycle:** caps and feature flags are stored but no enforcement/expiry/renewal processor is present.
10. **Analytics include presentation constants:** landing-page patient/satisfaction figures and super-admin platform health/compliance text include hard-coded or synthetic values. Treat them as display placeholders, not measured clinical or compliance claims.
11. **Payment semantics:** staff-entered payments are marked completed immediately; partial/overpayment behavior is largely permitted, with displayed balance clamped to zero. No refund workflow or payment provider exists.
12. **Data deletion behavior:** profiles are generally deactivated rather than deleted; foreign-key delete policies vary by model. Preserve medical/financial history and use explicit retention rules in a production port.
13. **Audit completeness:** only selected view actions write audit events; the logger suppresses failures. A production audit requirement needs reliable transactional logging, restricted mutation, retention, and monitoring.
14. **Sensitive health data:** implement least-privilege access, authentication for patient records, secure uploads, encryption/backups, access logging, retention policies, and production secrets/configuration before using real patient data. The checked-in Django settings are development settings, not production-ready.

## 10. Suggested porting sequence

1. Define tenant boundaries and whether users can belong to more than one hospital.
2. Implement account identity, hospital, membership, and server-side authorization first.
3. Create the relational schema with decimal money columns, foreign keys, tenant-scoped uniqueness, and indexes for hospital/status/date lookups.
4. Implement departments, doctor/staff/patient profiles and availability.
5. Implement booking with transactional conflict prevention and explicit validation of hospital/doctor/department/time/availability.
6. Add consultation records, prescriptions, lab orders/reports, then notifications and reliable audit events.
7. Add invoices, line items, payment reconciliation, and explicitly defined refund/overpayment rules.
8. Add role-specific dashboards and analytics only after the underlying data rules are stable.
9. Rebuild public pages and patient self-service with authentication/consent appropriate to the target jurisdiction.
10. Port seeded sample data only with non-production credentials and keep all secrets/configuration outside source control.

## 11. Minimum behavior checks for a port

- Correct redirect after login for all six roles; reject wrong-role portal login and inactive users.
- A user cannot access another hospital's patient, appointment, clinical, lab, or billing records by changing an object ID.
- A patient can see only their own records after authentication.
- Appointment overlap detection handles containment, partial overlap, exact match, cancelled/no-show appointments, and simultaneous booking attempts.
- Appointment cancellation requires a reason; creating a consultation record completes the appointment.
- Prescription medicines cannot be changed after issue/cancellation; issue notification is generated once per intended action.
- Lab report upload links to the correct order/patient/hospital and completes the order.
- Invoice line arithmetic and invoice-level arithmetic use decimal precision and server-side calculations; payment status/balance remains correct for partial, exact, excess, void, and refunded cases.
- Hospital and user deactivation does not accidentally erase protected medical/financial history.
- Audit and notification failures are observable and do not silently masquerade as success.
