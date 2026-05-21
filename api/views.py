from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import os
from api.models import Building, UserProfile, EmergencyAlert, UserAlertConfirmation, AlertLog
from api.serializers import (
    UserSerializer, UserProfileSerializer, BuildingSerializer,
    EmergencyAlertSerializer, EmergencyAlertCreateSerializer,
    UserAlertConfirmationSerializer, AlertLogSerializer
)
import firebase_admin
from firebase_admin import credentials, messaging


def _send_fcm_multicast(tokens, title, body, payload):
    """Best-effort FCM send. Returns (success_count, error_message)."""
    if not tokens:
        return 0, None

    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    if not os.path.exists(cred_path):
        return 0, f"Firebase credentials tidak ditemukan di: {cred_path}"

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        msg = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=title, body=body[:120]),
            data={k: str(v) for k, v in payload.items()},
            android=messaging.AndroidConfig(priority="high"),
        )
        result = messaging.send_each_for_multicast(msg)
        return result.success_count, None
    except Exception as exc:
        return 0, str(exc)


class BuildingViewSet(viewsets.ModelViewSet):
    """ViewSet untuk Building"""
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet untuk UserProfile"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user profile"""
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def active_users(self, request):
        """Get all active users"""
        profiles = UserProfile.objects.filter(status='active')
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_users(self, request):
        """Get all pending users"""
        profiles = UserProfile.objects.filter(status='pending')
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)


class EmergencyAlertViewSet(viewsets.ModelViewSet):
    """ViewSet untuk EmergencyAlert"""
    queryset = EmergencyAlert.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmergencyAlertCreateSerializer
        return EmergencyAlertSerializer
    
    def perform_create(self, serializer):
        """Create alert dengan triggered_by sebagai current user"""
        serializer.save(triggered_by=self.request.user)
        alert = serializer.instance

        active_profiles = UserProfile.objects.select_related("user").filter(status="active")
        confirmations = [
            UserAlertConfirmation(alert=alert, user=profile.user, building=alert.building, status='no_response')
            for profile in active_profiles
        ]
        if confirmations:
            UserAlertConfirmation.objects.bulk_create(confirmations, ignore_conflicts=True)

        tokens = [p.fcm_token for p in active_profiles if p.fcm_token]
        sent_count, fcm_error = _send_fcm_multicast(
            tokens=tokens,
            title=f"ALARM DARURAT: {alert.title}",
            body=alert.description,
            payload={
                "type": "emergency",
                "alert_id": alert.id,
                "title": alert.title,
                "message": alert.description,
            },
        )
        
        # Create log
        AlertLog.objects.create(
            alert=alert,
            building=alert.building,
            action='created',
            description='Alert darurat dibuat oleh operator',
            performed_by=self.request.user
        )
        AlertLog.objects.create(
            alert=alert,
            building=alert.building,
            action='sent',
            description=f'Notifikasi dikirim ke {sent_count}/{len(tokens)} device aktif.'
            + (f' FCM fallback: {fcm_error}' if fcm_error else ''),
            performed_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark alert as resolved"""
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        # Create log
        AlertLog.objects.create(
            alert=alert,
            building=alert.building,
            action='resolved',
            description='Alert ditandai sebagai terselesaikan',
            performed_by=request.user
        )
        
        return Response({'status': 'Alert resolved'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel alert"""
        alert = self.get_object()
        alert.status = 'cancelled'
        alert.save()
        
        # Create log
        AlertLog.objects.create(
            alert=alert,
            building=alert.building,
            action='cancelled',
            description='Alert dibatalkan',
            performed_by=request.user
        )
        
        return Response({'status': 'Alert cancelled'})
    
    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """Get active alerts only"""
        alerts = EmergencyAlert.objects.filter(status='active')
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)


class UserAlertConfirmationViewSet(viewsets.ModelViewSet):
    """ViewSet untuk UserAlertConfirmation"""
    queryset = UserAlertConfirmation.objects.all()
    serializer_class = UserAlertConfirmationSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def confirm_status(self, request):
        """User confirm their status for an alert"""
        alert_id = request.data.get('alert_id')
        status_value = request.data.get('status')
        location = request.data.get('location', '')
        notes = request.data.get('notes', '')
        
        try:
            confirmation = UserAlertConfirmation.objects.get(
                alert_id=alert_id,
                user=request.user
            )
            confirmation.status = status_value
            confirmation.location = location
            confirmation.notes = notes
            confirmation.building = confirmation.alert.building
            confirmation.confirmed_at = timezone.now()
            confirmation.save()
            
            serializer = self.get_serializer(confirmation)
            return Response(serializer.data)
        except UserAlertConfirmation.DoesNotExist:
            return Response(
                {'error': 'Confirmation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def alert_confirmations(self, request):
        """Get confirmations for a specific alert"""
        alert_id = request.query_params.get('alert_id')
        if not alert_id:
            return Response(
                {'error': 'alert_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        confirmations = UserAlertConfirmation.objects.filter(alert_id=alert_id)
        serializer = self.get_serializer(confirmations, many=True)
        return Response(serializer.data)


class AlertLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet untuk AlertLog (read-only)"""
    queryset = AlertLog.objects.all()
    serializer_class = AlertLogSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def alert_logs(self, request):
        """Get logs for a specific alert"""
        alert_id = request.query_params.get('alert_id')
        if not alert_id:
            return Response(
                {'error': 'alert_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = AlertLog.objects.filter(alert_id=alert_id)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

