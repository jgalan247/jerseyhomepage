from django.urls import path
from . import views
from .views import EventSearchView  # Add this import

app_name = 'event_management'

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('search/', EventSearchView.as_view(), name='event_search'),
    path('event/<slug:slug>/', views.event_detail, name='event_detail'),
    path('create/', views.create_event, name='create_event'),
    path('list/', views.list_event_landing, name='list_event_landing'),
    path('event/<slug:slug>/download-ics/', views.download_ics, name='download_ics'),
]