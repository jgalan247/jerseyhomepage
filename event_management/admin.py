from django.contrib import admin
from .models import Category, Event, EventImage
from django.utils.html import format_html

#class EventImageInline(admin.TabularInline):
#    model = EventImage
#    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'category', 'date', 'venue', 'price', 
                    'is_approved', 'is_featured', 'is_active', 'status_display')
    list_filter = ('is_approved', 'category', 'is_featured', 'is_active', 'date')
    search_fields = ('title', 'description', 'venue', 'organizer__company_name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'date'
    
    # Highlighted pending approval events
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'organizer', 'approved_by')
    
    # Admin actions
    actions = ['approve_events', 'reject_events']
    
    def approve_events(self, request, queryset):
        count = 0
        for event in queryset.filter(is_approved=False):
            event.approve(request.user)
            count += 1
        self.message_user(request, f'{count} events approved.')
    approve_events.short_description = 'Approve selected events'
    
    def reject_events(self, request, queryset):
        count = queryset.update(
            is_approved=False,
            approved_by=None,
            approved_at=None
        )
        self.message_user(request, f'{count} events rejected.')
    reject_events.short_description = 'Reject selected events'
    
    # Custom display
    def status_display(self, obj):
        return obj.status_display
    status_display.short_description = 'Status'