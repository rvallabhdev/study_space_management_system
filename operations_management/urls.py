from django.urls import path
from . import views

app_name = 'operations_management'

urlpatterns = [
    path('enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/add/', views.enrollment_create, name='enrollment_create'),
    path('enrollments/<int:pk>/', views.enrollment_detail, name='enrollment_detail'),
    path('enrollments/<int:pk>/payment/', views.enrollment_payment, name='enrollment_payment'),
    path('enrollments/<int:pk>/cancel/', views.enrollment_cancel, name='enrollment_cancel'),
]