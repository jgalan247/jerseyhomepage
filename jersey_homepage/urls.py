"""
URL configuration for jersey_homepage project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from event_management.views import homepage, faq_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage, name='home'),  # Homepage at root
    path('faq/', faq_view, name='faq'),  
    path('auth/', include('authentication.urls')),
    path('booking/', include('booking.urls')),
    path('events/', include('event_management.urls')),
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