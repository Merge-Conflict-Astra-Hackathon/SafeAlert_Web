import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from api.models import Building, EmergencyAlert, UserAlertConfirmation, UserProfile


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
    active_profiles = list(
        UserProfile.objects.select_related("user", "building").exclude(status="pending")
    )
    active_alert = EmergencyAlert.objects.select_related("building", "triggered_by").filter(status="active").first()
    all_alerts = EmergencyAlert.objects.select_related("building", "triggered_by").all()[:20]
    buildings = Building.objects.all()
    latest_confirmation_by_user = {}

    latest_confirmations = (
        UserAlertConfirmation.objects.select_related("alert")
        .order_by("-confirmed_at", "-notified_at")
    )
    for confirmation in latest_confirmations:
        if confirmation.user_id not in latest_confirmation_by_user:
            latest_confirmation_by_user[confirmation.user_id] = confirmation

    for profile in active_profiles:
        latest_confirmation = latest_confirmation_by_user.get(profile.user_id)
        latest_status = latest_confirmation.status if latest_confirmation else ""
        profile.latest_emergency_note = latest_confirmation.notes if latest_confirmation else ""
        profile.latest_emergency_location = latest_confirmation.location if latest_confirmation else ""
        profile.latest_emergency_status = latest_status
        profile.latest_emergency_confirmation_id = latest_confirmation.id if latest_confirmation else None
        profile.latest_emergency_alert_title = latest_confirmation.alert.title if latest_confirmation else ""
        profile.latest_emergency_status_label = {
            "safe": "Aman",
            "needs_help": "Evakuasi",
            "trapped": "Terjebak",
            "no_response": "Belum Respon",
        }.get(latest_status, "Belum Ada Status")

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


def _building_payload(building):
    return {
        "id": building.id,
        "name": building.name,
        "address": building.address,
        "latitude": building.latitude,
        "longitude": building.longitude,
        "total_capacity": building.total_capacity,
        "user_count": building.userprofile_set.count(),
        "alert_count": building.alerts.count(),
        "created_at": building.created_at.strftime("%d %b %Y %H:%M"),
    }


@login_required(login_url="dashboard:login")
@require_http_methods(["POST"])
def building_create_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"message": "Format data tidak valid."}, status=400)

    name = str(payload.get("name", "")).strip()
    address = str(payload.get("address", "")).strip()
    total_capacity = payload.get("total_capacity") or 0
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")

    if not name or not address:
        return JsonResponse({"message": "Nama dan alamat gedung wajib diisi."}, status=400)

    try:
        total_capacity = int(total_capacity)
        latitude = float(latitude) if latitude not in (None, "") else None
        longitude = float(longitude) if longitude not in (None, "") else None
    except (TypeError, ValueError):
        return JsonResponse({"message": "Kapasitas, latitude, atau longitude tidak valid."}, status=400)

    building = Building.objects.create(
        name=name,
        address=address,
        total_capacity=total_capacity,
        latitude=latitude,
        longitude=longitude,
    )
    return JsonResponse({"message": "Gedung berhasil ditambahkan.", "building": _building_payload(building)}, status=201)


@login_required(login_url="dashboard:login")
@require_http_methods(["PATCH", "DELETE"])
def building_detail_api(request, building_id):
    try:
        building = Building.objects.get(id=building_id)
    except Building.DoesNotExist:
        return JsonResponse({"message": "Gedung tidak ditemukan."}, status=404)

    if request.method == "DELETE":
        if building.userprofile_set.exists() or building.alerts.exists():
            return JsonResponse(
                {"message": "Gedung masih dipakai user atau riwayat alarm, jadi tidak bisa dihapus."},
                status=400,
            )
        building.delete()
        return JsonResponse({"message": "Gedung berhasil dihapus."})

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"message": "Format data tidak valid."}, status=400)

    name = str(payload.get("name", "")).strip()
    address = str(payload.get("address", "")).strip()
    total_capacity = payload.get("total_capacity") or 0
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")

    if not name or not address:
        return JsonResponse({"message": "Nama dan alamat gedung wajib diisi."}, status=400)

    try:
        building.total_capacity = int(total_capacity)
        building.latitude = float(latitude) if latitude not in (None, "") else None
        building.longitude = float(longitude) if longitude not in (None, "") else None
    except (TypeError, ValueError):
        return JsonResponse({"message": "Kapasitas, latitude, atau longitude tidak valid."}, status=400)

    building.name = name
    building.address = address
    building.save()
    return JsonResponse({"message": "Gedung berhasil diperbarui.", "building": _building_payload(building)})
