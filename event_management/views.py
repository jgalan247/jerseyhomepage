# event_management/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Event, Category

def event_list(request):
    events = Event.objects.filter(is_active=True, date__gte=timezone.now())
    categories = Category.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(venue__icontains=search_query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        events = events.filter(category__slug=category_slug)
    
    # Quick filters
    filter_type = request.GET.get('filter')
    if filter_type == 'free':
        events = events.filter(price=0)
    elif filter_type == 'weekend':
        events = events.filter(date__week_day__in=[6, 7, 1])
    elif filter_type == 'pet-friendly':
        events = events.filter(pet_friendly=True)
    elif filter_type == 'family-friendly':
        events = events.filter(family_friendly=True)
    
    # Pagination
    paginator = Paginator(events, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_slug,
        'selected_filter': filter_type,
        'total_events': paginator.count,
    }
    
    return render(request, 'event_management/event_list.html', context)

def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    related_events = Event.objects.filter(
        category=event.category,
        is_active=True,
        date__gte=timezone.now()
    ).exclude(id=event.id)[:3]
    
    context = {
        'event': event,
        'related_events': related_events,
    }
    
    return render(request, 'event_management/event_detail.html', context)

# Placeholder views for future functionality
def create_event(request):
    """Create a new event"""
    return render(request, 'event_management/create_event.html', {})

def list_event_landing(request):
    """Landing page for listing events"""
    return render(request, 'event_management/list_event_landing.html', {})