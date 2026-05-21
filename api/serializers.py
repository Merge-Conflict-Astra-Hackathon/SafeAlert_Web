from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import Building, UserProfile, EmergencyAlert, UserAlertConfirmation, AlertLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer untuk User"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detail serializer untuk User dengan profile"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']


class BuildingSerializer(serializers.ModelSerializer):
    """Serializer untuk Building"""
    class Meta:
        model = Building
        fields = ['id', 'name', 'address', 'latitude', 'longitude', 'total_capacity', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer untuk UserProfile"""
    user = UserSerializer(read_only=True)
    building = BuildingSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'building', 'phone_number', 'disability_type', 'special_needs', 
                 'status', 'fcm_token', 'is_inside_building', 'last_location', 'created_at', 'updated_at']


class AlertLogSerializer(serializers.ModelSerializer):
    """Serializer untuk AlertLog"""
    performed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = AlertLog
        fields = ['id', 'alert', 'action', 'description', 'performed_by', 'timestamp']


class UserAlertConfirmationSerializer(serializers.ModelSerializer):
    """Serializer untuk UserAlertConfirmation"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserAlertConfirmation
        fields = ['id', 'alert', 'user', 'status', 'location', 'notes', 'notified_at', 'confirmed_at']


class EmergencyAlertSerializer(serializers.ModelSerializer):
    """Serializer untuk EmergencyAlert"""
    triggered_by = UserSerializer(read_only=True)
    building = BuildingSerializer(read_only=True)
    user_confirmations = UserAlertConfirmationSerializer(many=True, read_only=True)
    logs = AlertLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmergencyAlert
        fields = ['id', 'building', 'alert_type', 'title', 'description', 'status', 'severity',
                 'triggered_by', 'created_at', 'updated_at', 'resolved_at', 'user_confirmations', 'logs']


class EmergencyAlertCreateSerializer(serializers.ModelSerializer):
    """Serializer untuk membuat EmergencyAlert"""
    class Meta:
        model = EmergencyAlert
        fields = ['building', 'alert_type', 'title', 'description', 'severity']
