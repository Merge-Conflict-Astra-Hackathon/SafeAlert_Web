from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api import views

router = DefaultRouter()
router.register(r'buildings', views.BuildingViewSet)
router.register(r'auth', views.MobileAuthViewSet, basename='mobile-auth')
router.register(r'users', views.UserProfileViewSet)
router.register(r'alerts', views.EmergencyAlertViewSet)
router.register(r'confirmations', views.UserAlertConfirmationViewSet)
router.register(r'logs', views.AlertLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
