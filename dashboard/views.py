from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from api.models import Building, EmergencyAlert, UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard:home")
        error = "Username atau password salah."

    return render(request, "login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("dashboard:login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    error = None
    success = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        full_name = request.POST.get("full_name", "").strip()

        if not username or not password:
            error = "Username dan password wajib diisi."
        elif password != password_confirm:
            error = "Konfirmasi password tidak sama."
        elif User.objects.filter(username=username).exists():
            error = "Username sudah digunakan."
        else:
            first_name, last_name = "", ""
            if full_name:
                parts = full_name.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
            )
            login(request, user)
            success = "Akun berhasil dibuat."
            return redirect("dashboard:home")

    return render(request, "register.html", {"error": error, "success": success})


@login_required(login_url="dashboard:login")
def dashboard_view(request):
    pending_users = UserProfile.objects.select_related("user", "building").filter(status="pending")
    active_profiles = UserProfile.objects.select_related("user", "building").exclude(status="pending")
    active_alert = EmergencyAlert.objects.select_related("building", "triggered_by").filter(status="active").first()
    all_alerts = EmergencyAlert.objects.select_related("building", "triggered_by").all()[:20]
    buildings = Building.objects.all()

    context = {
        "pending_users": pending_users,
        "active_profiles": active_profiles,
        "active_alert": active_alert,
        "all_alerts": all_alerts,
        "buildings": buildings,
        "total_users": UserProfile.objects.count(),
        "active_users": UserProfile.objects.filter(status="active").count(),
        "pending_count": pending_users.count(),
        "active_alerts_count": EmergencyAlert.objects.filter(status="active").count(),
    }
    return render(request, "dashboard.html", context)


@login_required(login_url="dashboard:login")
def dashboard_stats_api(request):
    data = {
        "total_users": UserProfile.objects.count(),
        "active_users": UserProfile.objects.filter(status="active").count(),
        "pending_users": UserProfile.objects.filter(status="pending").count(),
        "active_alerts": EmergencyAlert.objects.filter(status="active").count(),
    }
    return JsonResponse(data)
