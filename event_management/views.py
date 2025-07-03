from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event
from authentication.models import Organizer

def homepage(request):
    return render(request, 'home.html')

@login_required
def organizer_dashboard(request):
    if not hasattr(request.user, 'organizer'):
        messages.error(request, 'You need to be an organizer to access this page.')
        return redirect('home')
    
    events = Event.objects.filter(organizer=request.user.organizer)
    return render(request, 'event_management/organizer_dashboard.html', {
        'events': events,
        'organizer': request.user.organizer
    })

@login_required
def create_event(request):
    if not hasattr(request.user, 'organizer'):
        messages.error(request, 'You need to be an organizer to create events.')
        return redirect('home')
    
    from .models import Category
    from .forms import EventForm
    
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user.organizer
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('event_management:organizer_dashboard')
    else:
        form = EventForm()
    
    return render(request, 'event_management/create_event.html', {
        'form': form,
        'categories': Category.objects.all()
    })

def event_list(request):
    events = Event.objects.filter(status='approved')
    return render(request, 'event_management/event_list.html', {'events': events})


def event_pricing(request):
    return render(request, 'event_management/pricing_info.html')


def event_detail(request, slug):
    from django.shortcuts import get_object_or_404
    event = get_object_or_404(Event, slug=slug)
    return render(request, 'event_management/event_detail.html', {
        'event': event
    })

def event_search(request):
    from django.shortcuts import redirect
    # Simple search redirect to event list with search param
    return redirect('event_management:event_list')


def download_ics(request, slug):
    from django.http import HttpResponse
    from django.shortcuts import get_object_or_404
    import datetime
    
    event = get_object_or_404(Event, slug=slug)
    
    # Create ICS content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Jersey Events//EN
BEGIN:VEVENT
UID:{event.id}@jerseyevents.com
DTSTAMP:{datetime.datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{event.date.strftime('%Y%m%dT%H%M%S')}
DTEND:{event.end_date.strftime('%Y%m%dT%H%M%S') if event.end_date else event.date.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{event.title}
DESCRIPTION:{event.description[:100]}...
LOCATION:{event.venue}, {event.address}
END:VEVENT
END:VCALENDAR"""
    
    response = HttpResponse(ics_content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{event.slug}.ics"'
    return response
