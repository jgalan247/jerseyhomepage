from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
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
    if request.user.is_authenticated:
        return redirect('event_management:event_list')
    
    # Using Django's built-in AuthenticationForm instead of CustomLoginForm
    form = AuthenticationForm(request, data=request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            
            # Redirect to next URL if provided, otherwise event_list
            next_url = request.GET.get('next', 'event_management:event_list')
            return redirect(next_url)
    
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