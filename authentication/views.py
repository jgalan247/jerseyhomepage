from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import SignUpForm, CustomLoginForm
from authentication.models import User

User = get_user_model()


def home(request):
    context = {
        'title': 'Welcome to Jersey Homepage',
        'message': 'Your gateway to discovering amazing events in Jersey!'
    }
    return render(request, 'home.html', context)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('login')
    else:
        form = SignUpForm()
    
    return render(request, 'events/auth/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = CustomLoginForm(request, data=request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    
    return render(request, 'events/auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    return render(request, 'events/auth/profile.html', {'user': request.user})


def verify_email_view(request, uidb64, token):
    messages.info(request, 'Email verification feature coming soon.')
    return redirect('home')


@login_required
def resend_verification_view(request):
    messages.info(request, 'Resend verification feature coming soon.')
    return redirect('home')


def privacy_policy(request):
    return render(request, 'events/legal/privacy_policy.html')


def terms_conditions(request):
    return render(request, 'events/legal/terms_conditions.html')

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
        return redirect('login')
    
    return render(request, 'events/create_event.html', {
        'title': 'Create Event',
        'message': 'Event creation coming in Milestone 5'
    })


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
        return redirect('login')
    
    return render(request, 'events/create_event.html', {
        'title': 'Create Event',
        'message': 'Event creation coming in Milestone 5'
    })


def list_event_landing(request):
    """Landing page for users wanting to list events"""
    return render(request, 'events/list_event_landing.html', {
        'title': 'List Your Event on Jersey Homepage'
    })
