from django import forms
from patients.models import PatientProfile
from appointments.models import Appointment
from .models import Invoice, InvoiceItem, Payment


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "patient",
            "appointment",
            "invoice_number",
            "due_date",
            "discount_amount",
            "tax_amount",
            "notes",
        ]
        widgets = {
            "invoice_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Leave blank to auto-generate (e.g. INV-2026-0001)",
            }),
            "due_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "discount_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "0.00",
            }),
            "tax_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "0.00",
            }),
            "notes": forms.Textarea(attrs={
                "rows": 2,
                "class": "form-control",
                "placeholder": "Payment terms, insurance remarks, or special instructions...",
            }),
        }

    def __init__(self, *args, hospital=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["invoice_number"].required = False
        self.fields["discount_amount"].required = False
        self.fields["tax_amount"].required = False

        if hospital:
            self.fields["patient"].queryset = PatientProfile.objects.filter(
                hospital=hospital, is_active=True
            ).select_related("user")
            self.fields["appointment"].queryset = Appointment.objects.filter(
                hospital=hospital
            ).select_related("patient", "doctor")
            self.fields["appointment"].required = False

        self.fields["patient"].widget.attrs.update({"class": "form-select"})
        self.fields["appointment"].widget.attrs.update({"class": "form-select"})

        self.fields["patient"].label_from_instance = (
            lambda obj: f"{obj.user.get_full_name() if obj.user else 'Patient'} ({obj.patient_id_code})"
        )
        self.fields["appointment"].label_from_instance = (
            lambda obj: f"Appt #{obj.pk} — {obj.patient.user.get_full_name() if obj.patient.user else 'Patient'} with Dr. {obj.doctor.user.get_full_name() if obj.doctor and obj.doctor.user else 'Doctor'} ({obj.start_at.strftime('%Y-%m-%d %H:%M')})"
        )


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = [
            "description",
            "item_type",
            "quantity",
            "unit_price",
            "discount_amount",
            "tax_amount",
        ]
        widgets = {
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Item description (e.g. Consultation Fee, CBC Blood Test, Paracetamol)",
            }),
            "item_type": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0.01",
                "step": "1",
                "value": "1",
            }),
            "unit_price": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "0.00",
            }),
            "discount_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "value": "0.00",
            }),
            "tax_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "value": "0.00",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["discount_amount"].required = False
        self.fields["tax_amount"].required = False


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "amount",
            "payment_method",
            "transaction_reference",
            "notes",
        ]
        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0.01",
                "step": "0.01",
                "placeholder": "Payment amount",
            }),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "transaction_reference": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Txn ID / Cheque # / Card Auth Code",
            }),
            "notes": forms.Textarea(attrs={
                "rows": 2,
                "class": "form-control",
                "placeholder": "Payer notes, remarks...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transaction_reference"].required = False
        self.fields["notes"].required = False
