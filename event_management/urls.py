# event_management/urls.py
from django.urls import path
from . import views

app_name = 'event_management'

urlpatterns = [
    # Comment out all URLs temporarily to get Django working
    # Uncomment and add missing view functions one by one later
    
    # path('', views.event_list, name='event_list'),
    # path('search/', views.EventSearchView.as_view(), name='event_search'),
    # path('list/', views.list_event_landing, name='list_event_landing'),
    # path('newsletter/', views.newsletter_signup, name='newsletter_signup'),
    # path('create/', views.create_event, name='create_event'),
    # path('<int:event_id>/tickets/', views.event_ticket_types, name='event_ticket_types'),
    # path('<int:event_id>/plan/', views.choose_plan, name='choose_plan'),
    # path('api/calculate-fee/', views.calculate_fee_ajax, name='calculate_fee_ajax'),
    # path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    # path('organizer/events/create/', views.create_event, name='organizer_create_event'),
    # path('organizer/events/<slug:slug>/edit/', views.edit_event, name='edit_event'),
    # path('organizer/events/<slug:slug>/delete/', views.delete_event, name='delete_event'),
    # path('become-organizer/', views.become_organizer, name='become_organizer'),
    # path('<slug:slug>/', views.event_detail, name='event_detail'),
    # path('<slug:slug>/download-ics/', views.download_ics, name='download_ics'),
]

# TODO: Add back URLs one by one as you create the corresponding view functions