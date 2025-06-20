from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignUpForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from django.contrib import messages
from .forms import SignUpForm
from django.core.mail import send_mail
from .forms import SignUpForm
from django.template.loader import render_to_string
from .forms import SignUpForm
from django.contrib.sites.shortcuts import get_current_site
from .forms import SignUpForm
from django.conf import settings
from .forms import SignUpForm
from django.views.decorators.http import require_http_methods
from .forms import SignUpForm
from django.http import JsonResponse
from .forms import SignUpForm


User = get_user_model()


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('event_management:event_list')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data.get('is_organizer'):
                messages.success(request, 'Organizer account created successfully! Please check your email to verify your account. You can now login and start creating events.')
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
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('event_management:event_list')


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

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email confirmed
            user.save()
            
            # Send verification email
            current_site = get_current_site(request)
            subject = 'Verify your Jersey Events account'
            message = render_to_string('authentication/verify_email.html', {
                'user': user,
                'domain': current_site.domain,
                'token': user.email_verification_token,
            })
            
            send_mail(
                subject,
                message,
                'noreply@jerseyevents.com',
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Please check your email to verify your account.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'authentication/register.html', {'form': form})

def verify_email(request, token):
    try:
        users = User.objects.filter(email_verification_token=token)
        
        if users.count() > 1:
            messages.error(request, 'There was an issue with your verification link. Please contact support.')
            return redirect('home')  # This one doesn't need namespace since it's in main urls
        
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
        
        # Use namespace:name format
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