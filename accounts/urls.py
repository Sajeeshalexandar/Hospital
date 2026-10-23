from django.urls import path
from . import views

# No app_name namespace here — Django's LOGIN_URL setting uses plain 'login'
# and our decorators use redirect('login'). Keeping names simple.

urlpatterns = [
    path("login/",  views.login_view,  name="login"),
    path("logout/", views.logout_view, name="logout"),
]
