from django.urls import path
from . import views
from .views import EventSearchView  # Add this import

app_name = 'event_management'

urlpatterns = [
    path('', views.event_list, name='event_list'),  # /events/
    path('search/', EventSearchView.as_view(), name='event_search'),  # /events/search/
    path('<slug:slug>/', views.event_detail, name='event_detail'),  # /events/jersey-food-festival/
    path('create/', views.create_event, name='create_event'),  # /events/create/
    path('list/', views.list_event_landing, name='list_event_landing'),  # /events/list/
    path('newsletter/', views.newsletter_signup, name='newsletter_signup'),
    path('<slug:slug>/download-ics/', views.download_ics, name='download_ics'),  # /events/jersey-food-festival/download-ics/
]