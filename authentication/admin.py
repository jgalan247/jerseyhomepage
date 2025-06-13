# authentication/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Organizer

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'date_of_birth', 'email_verified')
        }),
    )

@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'is_verified', 'stripe_account_id', 'created_at']
    list_filter = ['is_verified', 'stripe_onboarding_complete']
    search_fields = ['company_name', 'user__email']