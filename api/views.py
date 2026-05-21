from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
import os
import json
from api.models import Building, UserProfile, EmergencyAlert, UserAlertConfirmation, AlertLog
from api.serializers import (
    UserSerializer, UserProfileSerializer, BuildingSerializer,
    EmergencyAlertSerializer, EmergencyAlertCreateSerializer,
    UserAlertConfirmationSerializer, AlertLogSerializer
)
import firebase_admin
from firebase_admin import credentials, messaging


def _user_payload(user):
    profile = getattr(user, "profile", None)
    building = profile.building if profile else None
    return {
        "id": user.id,
        "name": user.get_full_name() or user.username,
        "phone": profile.phone_number if profile else user.username,
        "admin_status": profile.status if profile else "active",
        "floor": profile.last_location if profile else "",
        "building_id": building.id if building else None,
        "building_name": building.name if building else "",
        "floor_plan": building.floor_plan.url if building and building.floor_plan else "",
    }


def _token_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _default_building():
    building = Building.objects.first()
    if building:
        return building
    return Building.objects.create(
        name="SafeAlert Building",
        address="Default location",
        total_capacity=0,
    )


def _send_fcm_multicast(tokens, title, body, payload):
    """Best-effort FCM send. Returns (success_count, error_message)."""
    if not tokens:
        return 0, None

    try:
        if not firebase_admin._apps:
            firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()
            if firebase_credentials_json:
                cred = credentials.Certificate(json.loads(firebase_credentials_json))
            else:
                cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
                if not os.path.exists(cred_path):
                    return 0, f"Firebase credentials tidak ditemukan di: {cred_path}"
                cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        msg = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=title, body=body[:120]),
            data={k: str(v) for k, v in payload.items()},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body[:120],
                    channel_id="safealert_emergency",
                    click_action="FLUTTER_NOTIFICATION_CLICK",
                    priority="max",
                    default_sound=True,
                    default_vibrate_timings=True,
                    visibility="public",
                ),
            ),
        )
        result = messaging.send_each_for_multicast(msg)
        return result.success_count, None
    except Exception as exc:
        return 0, str(exc)


class BuildingViewSet(viewsets.ModelViewSet):
    """ViewSet untuk Building"""
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


class MobileAuthViewSet(viewsets.ViewSet):
    """Endpoint kompatibel untuk aplikasi Flutter mobile."""
    permission_classes = [AllowAny]

    def _first_present(self, data, *keys, default=''):
        for key in keys:
            value = data.get(key)
            if value is not None:
                return value
        return default

    def _clean_text(self, value):
        return str(value or '').strip()

    @action(detail=False, methods=['post'])
    def register(self, request):
        name = self._clean_text(
            self._first_present(request.data, 'name', 'full_name', 'nama', 'username')
        )
        phone = self._clean_text(
            self._first_present(request.data, 'phone', 'phone_number', 'no_hp', 'nomor_hp')
        )
        password = str(request.data.get('password') or '')
        floor = self._first_present(request.data, 'floor', 'lantai')
        building_id = self._first_present(
            request.data, 'building_id', 'buildingId', 'building'
        )
        disability_type = self._clean_text(
            self._first_present(request.data, 'disability_type', 'disabilityType', default='none')
        ) or 'none'
        if disability_type == 'mobility':
            disability_type = 'other'
        fcm_token = self._clean_text(
            self._first_present(request.data, 'fcm_token', 'fcmToken')
        )

        if not name or not phone or not password or not building_id:
            return Response(
                {'message': 'Nama, nomor HP, password, dan gedung wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            building = Building.objects.get(id=building_id)
        except (Building.DoesNotExist, ValueError, TypeError):
            return Response(
                {'message': 'Gedung tidak valid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=phone).exists():
            return Response(
                {'message': 'Nomor HP sudah terdaftar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parts = name.split(" ", 1)
        user = User.objects.create_user(
            username=phone,
            password=password,
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else "",
        )
        UserProfile.objects.create(
            user=user,
            building=building,
            phone_number=phone,
            disability_type=disability_type,
            status='pending',
            fcm_token=fcm_token,
            last_location=str(floor) if floor else "",
        )

        return Response(
            {
                "data": _user_payload(user),
                "tokens": _token_payload(user),
                "message": "Registrasi berhasil. Akun menunggu verifikasi admin.",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def login(self, request):
        phone = request.data.get('phone', '').strip()
        password = request.data.get('password', '')
        fcm_token = request.data.get('fcm_token', '')

        user = authenticate(request, username=phone, password=password)
        if not user:
            return Response(
                {'message': 'Nomor HP atau password salah.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "building": _default_building(),
                "phone_number": phone,
                "status": "active",
            },
        )
        if fcm_token:
            profile.fcm_token = fcm_token
            profile.save(update_fields=["fcm_token", "updated_at"])

        return Response(
            {
                "data": _user_payload(user),
                "tokens": _token_payload(user),
                "message": "Login berhasil.",
            }
        )


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

    @action(detail=False, methods=['patch'])
    def update_floor(self, request):
        """Update only the current user's floor/location number."""
        floor = str(request.data.get('floor', '')).strip()
        if not floor:
            return Response(
                {'message': 'Nomor lantai wajib diisi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            floor_number = int(floor)
        except ValueError:
            return Response(
                {'message': 'Nomor lantai harus berupa angka.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if floor_number < 0 or floor_number > 200:
            return Response(
                {'message': 'Nomor lantai tidak valid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "building": _default_building(),
                "phone_number": request.user.username,
                "status": "active",
            },
        )
        profile.last_location = str(floor_number)
        profile.save(update_fields=["last_location", "updated_at"])

        return Response({
            'message': 'Nomor lantai berhasil diperbarui.',
            'data': _user_payload(request.user),
        })


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

        active_profiles = UserProfile.objects.select_related("user").filter(
            status="active",
            building=alert.building,
        )
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
                "alarm_id": alert.id,
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
        """Get active alerts that still need this user response."""
        alerts = EmergencyAlert.objects.filter(status='active')
        if not request.user.is_staff and not request.user.is_superuser:
            alerts = alerts.filter(
                user_confirmations__user=request.user,
                user_confirmations__status='no_response',
            )
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

