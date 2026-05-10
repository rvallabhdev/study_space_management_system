"""
URL configuration for study_space_management_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin interface
    path('admin/', admin.site.urls),

    # Study Space Management app – handles students, spaces, seats, time slots, Gantt chart
    path('', include('study_space_management.urls')),

    # User authentication – login, logout, registration
    path('auth/', include('user_management.urls')),

    # Operations Management – enrollments (student allocation to seats)
    path('operations/', include('operations_management.urls')),
]

# Serve media (user‑uploaded files) and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)