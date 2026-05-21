from django.contrib import admin

from api.models import AlertLog, Building, EmergencyAlert, UserAlertConfirmation, UserProfile


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "floor_plan", "created_at")
    search_fields = ("name", "address")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "building", "disability_type", "status", "last_location")
    list_filter = ("status", "disability_type", "building")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone_number")
    readonly_fields = ("created_at", "updated_at")


@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ("title", "building", "alert_type", "status", "severity", "triggered_by", "created_at")
    list_filter = ("status", "alert_type", "severity", "building")
    search_fields = ("title", "description", "building__name")
    readonly_fields = ("created_at", "updated_at", "resolved_at")


@admin.register(UserAlertConfirmation)
class UserAlertConfirmationAdmin(admin.ModelAdmin):
    list_display = ("alert", "user", "building", "status", "location", "notified_at", "confirmed_at")
    list_filter = ("status", "building", "notified_at")
    search_fields = ("alert__title", "user__username", "location", "notes")
    readonly_fields = ("notified_at", "confirmed_at")


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ("alert", "building", "action", "performed_by", "timestamp")
    list_filter = ("action", "building", "timestamp")
    search_fields = ("alert__title", "description", "performed_by__username")
    readonly_fields = ("timestamp",)
