from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.decorators import hospital_admin_required
from accounts.helpers import get_user_hospital
from .models import Department
from .forms import DepartmentForm


@hospital_admin_required
def department_list(request):
    """Hospital Admin: list all departments in their hospital."""
    hospital    = get_user_hospital(request.user)
    departments = Department.objects.filter(hospital=hospital).order_by("name")

    context = {
        "hospital": hospital,
        "departments": departments,
    }
    return render(request, "hospital_admin/departments/list.html", context)


@hospital_admin_required
def department_create(request):
    """
    Hospital Admin: create a new department.
    The hospital is taken from the user's membership — NEVER from the form.
    """
    hospital = get_user_hospital(request.user)
    form     = DepartmentForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            dept = form.save(commit=False)
            dept.hospital = hospital   # ← set hospital from DB, not form
            dept.save()
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect("department_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "hospital": hospital, "action": "Create"}
    return render(request, "hospital_admin/departments/form.html", context)


@hospital_admin_required
def department_edit(request, pk):
    """
    Hospital Admin: edit a department.
    Verifies the department belongs to the user's own hospital before
    allowing any changes (tenant isolation).
    """
    hospital = get_user_hospital(request.user)
    # get_object_or_404 with hospital= ensures cross-hospital access returns 404
    dept = get_object_or_404(Department, pk=pk, hospital=hospital)
    form = DepartmentForm(request.POST or None, instance=dept)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect("department_list")
        else:
            messages.error(request, "Please fix the errors below.")

    context = {"form": form, "hospital": hospital, "action": "Edit", "dept": dept}
    return render(request, "hospital_admin/departments/form.html", context)


@hospital_admin_required
def department_delete(request, pk):
    """
    Hospital Admin: delete a department.
    Ownership is always verified — a different hospital's department returns 404.
    """
    hospital = get_user_hospital(request.user)
    dept     = get_object_or_404(Department, pk=pk, hospital=hospital)

    if request.method == "POST":
        name = dept.name
        dept.delete()
        messages.success(request, f"Department '{name}' deleted.")
        return redirect("department_list")

    context = {"dept": dept, "hospital": hospital}
    return render(request, "hospital_admin/departments/confirm_delete.html", context)
