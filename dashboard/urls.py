from django.urls import path
from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("api/stats/", views.dashboard_stats_api, name="stats-api"),
]
