from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Building(models.Model):
    """Model untuk gedung/lokasi"""
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    total_capacity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    """Extended user profile untuk menyimpan informasi tambahan"""
    DISABILITY_CHOICES = [
        ('none', 'No Disability'),
        ('deaf', 'Deaf'),
        ('blind', 'Blind'),
        ('mobility', 'Mobility Impairment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending Verification'),
        ('blocked', 'Blocked'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    disability_type = models.CharField(max_length=20, choices=DISABILITY_CHOICES, default='none')
    special_needs = models.TextField(blank=True, help_text="Kebutuhan khusus pengguna")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fcm_token = models.TextField(blank=True, help_text="Firebase Cloud Messaging token")
    is_inside_building = models.BooleanField(default=False)
    last_location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    class Meta:
        ordering = ['-created_at']


class EmergencyAlert(models.Model):
    """Model untuk alert darurat"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    ALERT_TYPE_CHOICES = [
        ('fire', 'Fire'),
        ('earthquake', 'Earthquake'),
        ('medical', 'Medical Emergency'),
        ('security', 'Security Threat'),
        ('other', 'Other'),
    ]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    severity = models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Critical')], default=3)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='triggered_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.alert_type} - {self.title} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class UserAlertConfirmation(models.Model):
    """Model untuk tracking konfirmasi dari user terhadap alert"""
    STATUS_CHOICES = [
        ('no_response', 'No Response'),
        ('safe', 'Safe'),
        ('trapped', 'Trapped'),
        ('needs_help', 'Needs Help'),
    ]

    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, related_name='user_confirmations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alert_confirmations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='no_response')
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    notified_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"

    class Meta:
        ordering = ['-notified_at']
        unique_together = ['alert', 'user']


class AlertLog(models.Model):
    """Model untuk log semua aktivitas alert"""
    ACTION_CHOICES = [
        ('created', 'Alert Created'),
        ('sent', 'Alert Sent to Users'),
        ('confirmed', 'User Confirmed'),
        ('resolved', 'Alert Resolved'),
        ('cancelled', 'Alert Cancelled'),
    ]

    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alert} - {self.action}"

    class Meta:
        ordering = ['-timestamp']

