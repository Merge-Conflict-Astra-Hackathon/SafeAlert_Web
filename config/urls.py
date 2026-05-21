"""
URL configuration for SafeAlert config project.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: redirect('/dashboard/')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Serve static files during development and media uploads for demo deployments.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
