# event_management/urls.py
from django.urls import path
from . import views

app_name = 'event_management'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('pricing/', views.event_pricing, name='event-pricing'),
    path('search/', views.event_search, name='event_search'),
    path('create/', views.create_event, name='create_event'),
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('<slug:slug>/ics/', views.download_ics, name='download_ics'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),  # Keep slug at the end
]
