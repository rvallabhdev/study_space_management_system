from django.urls import path
from . import views

app_name = 'study_space_management'

urlpatterns = [
    # ==================== STUDENT URLs ====================
    path('', views.home, name='home'),
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_update, name='student_update'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),

    # ==================== STUDY SPACE URLs ====================
    path('spaces/', views.study_space_list, name='study_space_list'),
    path('spaces/add/', views.study_space_create, name='study_space_create'),
    path('spaces/<int:pk>/', views.study_space_detail, name='study_space_detail'),
    path('spaces/<int:pk>/edit/', views.study_space_update, name='study_space_update'),
    path('spaces/<int:pk>/delete/', views.study_space_delete, name='study_space_delete'),
    
    # ==================== SEAT URLs ====================
    path('seats/', views.seat_list, name='seat_list'),
    path('seats/add/', views.seat_create, name='seat_create'),
    path('seats/bulk-add/', views.bulk_seat_create, name='bulk_seat_create'),
    path('seats/<int:pk>/edit/', views.seat_update, name='seat_update'),
    path('seats/<int:pk>/delete/', views.seat_delete, name='seat_delete'),
    path('spaces/<int:study_space_id>/seats/', views.seat_list, name='seat_list_by_space'),

    # ==================== TIME SLOT URLs ====================
    path('time-slots/', views.time_slot_list, name='time_slot_list'),
    path('time-slots/add/', views.time_slot_create, name='time_slot_create'),
    path('time-slots/<int:pk>/edit/', views.time_slot_update, name='time_slot_update'),
    path('time-slots/<int:pk>/delete/', views.time_slot_delete, name='time_slot_delete'),
    path('time-slots/<int:pk>/toggle/', views.time_slot_toggle_status, name='time_slot_toggle'),

    # ==================== API ENDPOINTS ====================
    path('api/time-slots/', views.api_time_slots, name='api_time_slots'),
    path('api/available-seats/', views.api_available_seats, name='api_available_seats'),
    path('api/occupancy-data/', views.api_occupancy_data, name='api_occupancy_data'),

    # ==================== OCCUPANCY GANTT URLs ====================
    path('occupancy/', views.occupancy_gantt, name='occupancy_gantt'),
    path('occupancy/space/<int:study_space_id>/', views.occupancy_gantt, name='occupancy_gantt_space'),
]