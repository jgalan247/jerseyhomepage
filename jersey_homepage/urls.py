"""
URL configuration for jersey_homepage project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from event_management import views
# from event_management.views import homepage, faq_view  # Comment out for now

urlpatterns = [
    path('admin/', admin.site.urls),
   path('', views.homepage, name='home'),
    # path('faq/', faq_view, name='faq'),  # Comment out until function exists
    path('auth/', include('authentication.urls')),
    path('booking/', include('booking.urls')),
    path('events/', include('event_management.urls')),
    path('payments/', include('payments.urls')), 
]

# Debug toolbar
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass  # Debug toolbar not installed

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)