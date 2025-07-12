# authentication/admin.py - FIXED VERSION FOR NON-EDITABLE FIELDS

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Organizer
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['id']
    
    # Check for custom fields and handle editable vs non-editable
    additional_fieldset_fields = []
    additional_readonly_fields = []
    
    # Check email_verified field
    if hasattr(User, 'email_verified'):
        list_display.append('email_verified')
        list_filter.append('email_verified')
        
        # Check if email_verified is editable
        email_verified_field = User._meta.get_field('email_verified')
        if email_verified_field.editable:
            additional_fieldset_fields.append('email_verified')
        else:
            additional_readonly_fields.append('email_verified')
    
    # Check email_verification_token field
    if hasattr(User, 'email_verification_token'):
        # Check if email_verification_token is editable
        token_field = User._meta.get_field('email_verification_token')
        if token_field.editable:
            additional_fieldset_fields.append('email_verification_token')
        else:
            additional_readonly_fields.append('email_verification_token')
    
    # Set readonly_fields
    readonly_fields = BaseUserAdmin.readonly_fields + tuple(additional_readonly_fields)
    
    # Add custom fieldset only if we have editable additional fields
    if additional_fieldset_fields:
        fieldsets = BaseUserAdmin.fieldsets + (
            ('Email Verification', {
                'fields': tuple(additional_fieldset_fields)
            }),
        )
    else:
        fieldsets = BaseUserAdmin.fieldsets
    
    # If we have readonly fields, add them to a readonly section
    if additional_readonly_fields:
        fieldsets = fieldsets + (
            ('Verification Info (Read-only)', {
                'fields': tuple(additional_readonly_fields),
                'classes': ('collapse',)
            }),
        )

@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    # Using ACTUAL field names that exist
    list_display = ['id', 'company_name', 'user_email', 'status_badge', 'created_at', 'admin_actions']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['company_name', 'user__email', 'user__first_name', 'user__last_name', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name',)
        }),
        ('User', {
            'fields': ('user',)
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_organizers', 'reject_organizers']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'No user'
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def status_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">⏳ Pending</span>'
        )
    status_badge.short_description = 'Status'
    
    def admin_actions(self, obj):
        if not obj.is_verified:
            return format_html(
                '<a class="button" href="{}" style="background-color: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Approve</a>',
                reverse('admin:approve_organizer', args=[obj.pk])
            )
        return format_html(
            '<span style="color: green;">✓ Approved</span>'
        )
    admin_actions.short_description = 'Quick Actions'
    
    def approve_organizers(self, request, queryset):
        count = 0
        for organizer in queryset.filter(is_verified=False):
            organizer.is_verified = True
            organizer.save()
            
            # Send approval email
            try:
                self.send_approval_email(organizer)
            except Exception as e:
                print(f"Error sending approval email: {e}")
            
            count += 1
            
        self.message_user(request, f'{count} organizer(s) approved and notified.')
    approve_organizers.short_description = 'Approve selected organizers'
    
    def reject_organizers(self, request, queryset):
        count = queryset.filter(is_verified=True).update(is_verified=False)
        self.message_user(request, f'{count} organizer(s) rejected.')
    reject_organizers.short_description = 'Reject selected organizers'
    
    def send_approval_email(self, organizer):
        """Send approval notification to organizer"""
        from django.core.mail import send_mail
        
        subject = 'Your Organizer Account Has Been Approved!'
        message = f'''
Dear {organizer.company_name},

Great news! Your organizer account on Jersey Homepage has been approved.

You can now:
- Create and manage events
- Sell tickets online
- Track your event performance

Login to your dashboard: {getattr(settings, 'SITE_URL', 'http://localhost:8000')}/organizer/dashboard/

Best regards,
Jersey Homepage Team
        '''
        
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jerseyhomepage.com'),
            [organizer.user.email],
            fail_silently=True,
        )
    
    def changelist_view(self, request, extra_context=None):
        # Add pending count to context
        extra_context = extra_context or {}
        extra_context['pending_count'] = Organizer.objects.filter(
            is_verified=False
        ).count()
        
        # Add custom title if there are pending organizers
        if extra_context['pending_count'] > 0:
            extra_context['title'] = f"Organizers ({extra_context['pending_count']} pending approval)"
        
        return super().changelist_view(request, extra_context=extra_context)


class OrganizerAdminWithUrls(OrganizerAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:organizer_id>/approve/',
                self.admin_site.admin_view(self.approve_organizer_view),
                name='approve_organizer',
            ),
        ]
        return custom_urls + urls
    
    def approve_organizer_view(self, request, organizer_id):
        organizer = get_object_or_404(Organizer, pk=organizer_id)
        
        if not organizer.is_verified:
            organizer.is_verified = True
            organizer.save()
            
            try:
                self.send_approval_email(organizer)
                messages.success(request, f'{organizer.company_name} has been approved and notified!')
            except Exception as e:
                messages.success(request, f'{organizer.company_name} has been approved! (Email notification failed)')
        else:
            messages.info(request, f'{organizer.company_name} is already approved.')
        
        return redirect('admin:authentication_organizer_changelist')

# Re-register with custom admin
admin.site.unregister(Organizer)
admin.site.register(Organizer, OrganizerAdminWithUrls)