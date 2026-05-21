from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import Building, UserProfile, EmergencyAlert, UserAlertConfirmation, AlertLog
from api.serializers import (
    UserSerializer, UserProfileSerializer, BuildingSerializer,
    EmergencyAlertSerializer, EmergencyAlertCreateSerializer,
    UserAlertConfirmationSerializer, AlertLogSerializer
)


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
        
        # Create log
        AlertLog.objects.create(
            alert=alert,
            action='created',
            description='Alert darurat dibuat oleh operator',
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

