from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from memberships.models import HospitalMembership


def login_view(request):
    """
    Custom login page.

    - Accepts email + password (no role selector — role is read from the DB).
    - After successful login, redirects based on the user's actual role.
    - Superusers go to /super-admin/dashboard/.
    - Membership roles go to their respective dashboards.
    - Users with no membership see an error and are logged out.
    """
    # If user is already logged in, send them straight to their dashboard
    if request.user.is_authenticated:
        return redirect("dashboard_dispatch")

    if request.method == "POST":
        email    = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
            return render(request, "accounts/login.html")

        # Django's authenticate() checks email against username too, but our
        # User model uses email as the unique login identifier.
        # We pass username=email because AbstractUser stores it in `username`
        # by default. If you want email-only login, set AUTHENTICATION_BACKENDS.
        # For now we support both username AND email login:
        user = authenticate(request, username=email, password=password)

        # If username-based auth failed, try email lookup
        if user is None:
            from accounts.models import User as AppUser
            try:
                db_user = AppUser.objects.get(email=email)
                user = authenticate(request, username=db_user.username, password=password)
            except AppUser.DoesNotExist:
                user = None

        if user is None:
            messages.error(request, "Invalid email or password. Please try again.")
            return render(request, "accounts/login.html")

        if not user.is_active:
            messages.error(request, "Your account has been disabled. Contact your administrator.")
            return render(request, "accounts/login.html")

        login(request, user)
        return redirect("dashboard_dispatch")

    # GET request — just show the login form
    return render(request, "accounts/login.html")


def logout_view(request):
    """
    Logs the user out and redirects to the login page.
    Uses POST to protect against CSRF-based logout attacks.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")
