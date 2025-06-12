from django.urls import path
from . import views

urlpatterns = [
    # Homepage - Event listing
    path('', views.event_list, name='home'),
    path('', views.event_list, name='event_list'),
    
    # Event detail
    path('event/<slug:slug>/', views.event_detail, name='event_detail'),
    
    # Event management (for later milestones)
    path('events/create/', views.create_event, name='create_event'),
    path('events/list/', views.list_event_landing, name='list_event_landing'),
]