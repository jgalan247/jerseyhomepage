from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .forms import SignUpForm, OrganizerRegistrationForm  # Add OrganizerRegistrationForm
from .models import Organizer  # Add this import
import uuid

User = get_user_model()


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('event_management:event_list')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # SEND VERIFICATION EMAIL
            send_verification_email(user, request)
            
            if form.cleaned_data.get('is_organizer'):
                messages.success(request, 'Organizer account created successfully! Please check your email to verify your account.')
            else:
                messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('authentication:login')
    else:
        form = SignUpForm()
    
    return render(request, 'authentication/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If that fails, try with email
        if user is None:
            try:
                # Find user by email
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            if user.email_verified:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Redirect based on user type
                if hasattr(user, 'organizer'):
                    return redirect('event_management:organizer_dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Please verify your email before logging in.')
        else:
            messages.error(request, 'Invalid credentials.')
    
    # Create form for display
    form = AuthenticationForm()
    form.fields['username'].widget.attrs.update({
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Username or Email'
    })
    form.fields['password'].widget.attrs.update({
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
        'placeholder': 'Password'
    })
    
    return render(request, 'authentication/login.html', {'form': form})

def logout_view(request):
    """Logout user and redirect to login"""
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        
        # Clear any existing messages before logout
        storage = messages.get_messages(request)
        storage.used = True
        
        logout(request)
        messages.success(request, f'You have been logged out successfully.')
    
    return redirect('authentication:login')


@login_required
def profile_view(request):
    return render(request, 'authentication/profile.html', {'user': request.user})


def verify_email_view(request, uidb64, token):
    messages.info(request, 'Email verification feature coming soon.')
    return redirect('event_management:event_list')


@login_required
def resend_verification_view(request):
    messages.info(request, 'Resend verification feature coming soon.')
    return redirect('event_management:event_list')


def privacy_policy(request):
    """Display privacy policy page"""
    return render(request, 'authentication/privacy_policy.html')


def terms_conditions(request):
    """Display terms and conditions page"""
    return render(request, 'authentication/terms_conditions.html')


def events_list(request):
    """List all events - placeholder for Milestone 3"""
    return render(request, 'events/events_list.html', {
        'title': 'All Events',
        'message': 'Events listing coming in Milestone 3'
    })


def create_event(request):
    """Create event - placeholder for Milestone 5"""
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to create an event.')
        return redirect('authentication:login')
    
    return render(request, 'events/create_event.html', {
        'title': 'Create Event',
        'message': 'Event creation coming in Milestone 5'
    })


def list_event_landing(request):
    """Landing page for users wanting to list events"""
    return render(request, 'events/list_event_landing.html', {
        'title': 'List Your Event on Jersey Homepage'
    })


def verify_email(request, token):
    try:
        users = User.objects.filter(email_verification_token=token)
        
        if users.count() > 1:
            messages.error(request, 'There was an issue with your verification link. Please contact support.')
            return redirect('home')
        
        user = users.first()
        
        if not user:
            messages.error(request, 'Invalid verification link.')
            return redirect('home')
        
        if not user.email_verified:
            user.email_verified = True
            user.is_active = True
            user.save()
            messages.success(request, 'Email verified successfully! You can now log in.')
        else:
            messages.info(request, 'Email already verified.')
        
        return redirect('authentication:login')
        
    except Exception as e:
        print(f"ERROR in verify_email: {str(e)}")
        messages.error(request, 'An error occurred during verification.')
        return redirect('home')


def send_verification_email(user, request=None):
    """Send email verification to user"""
    # Get current site domain
    if request:
        current_site = get_current_site(request)
        domain = current_site.domain
        protocol = 'https' if request.is_secure() else 'http'
    else:
        domain = 'localhost:8000'  # Fallback for testing
        protocol = 'http'
    
    # Create context for templates
    context = {
        'user': user,
        'domain': domain,
        'protocol': protocol,
        'verification_url': f"{protocol}://{domain}/auth/verify-email/{user.email_verification_token}/",
        'token': user.email_verification_token,
    }
    
    # Render email templates
    subject = render_to_string('authentication/emails/verify_email_subject.txt', context).strip()
    message = render_to_string('authentication/emails/verify_email_message.txt', context)
    html_message = render_to_string('authentication/emails/verify_email_message.html', context)
    
    # Send email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL or 'noreply@coderra.je',
        [user.email],
        fail_silently=False,
        html_message=html_message
    )


@login_required
def register_as_organizer(request):
    """Register current user as an organizer"""
    
    # Check if already an organizer
    try:
        organizer = request.user.organizer_profile
        messages.info(request, "You're already registered as an organizer!")
        return redirect('event_management:organizer_dashboard')
    except Organizer.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = OrganizerRegistrationForm(request.POST)
        if form.is_valid():
            organizer = form.save(commit=False)
            organizer.user = request.user
            organizer.is_verified = False  # Requires admin verification
            organizer.save()
            
            # Send admin notification
            messages.success(request, 
                "Your organizer application has been submitted! "
                "We'll review it and get back to you within 1-2 business days."
            )
            
            # Optional: Send email to admin
            # send_admin_notification_email(organizer)
            
            return redirect('home')
    else:
        form = OrganizerRegistrationForm()
    
    context = {
        'form': form
    }
    return render(request, 'authentication/register_organizer.html', context)