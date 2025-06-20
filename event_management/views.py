# event_management/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Event, Category
from django.views.generic import ListView
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.http import HttpResponse
from datetime import timedelta
from django.contrib import messages

def event_list(request):
    events = Event.objects.filter(is_active=True, date__gte=timezone.now())
    categories = Category.objects.all()
    
    # Enhanced search using PostgreSQL full-text search
    search_query = request.GET.get('search', '')
    if search_query:
        # Use PostgreSQL search if available
        try:
            search = SearchQuery(search_query)
            events = events.annotate(
                rank=SearchRank('search_vector', search)
            ).filter(search_vector=search).order_by('-rank')
        except:
            # Fallback to basic search if PostgreSQL search not available
            events = events.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(venue__icontains=search_query)
            )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        events = events.filter(category__slug=category_slug)
    
    # Date range filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        events = events.filter(date__gte=date_from)
    if date_to:
        events = events.filter(date__lte=date_to)
    
    # Price range filters
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        events = events.filter(price__gte=price_min)
    if price_max:
        events = events.filter(price__lte=price_max)
    
    # Quick filters - Using OR logic with Q objects
    selected_filters = request.GET.getlist('filter')  # Get multiple values
    
    if selected_filters:
        filter_query = Q()
        
        if 'free' in selected_filters:
            filter_query |= Q(price=0)
        if 'weekend' in selected_filters:
            filter_query |= Q(date__week_day__in=[6, 7, 1])
        if 'pet-friendly' in selected_filters:
            filter_query |= Q(pet_friendly=True)
        if 'family-friendly' in selected_filters:
            filter_query |= Q(family_friendly=True)
        if 'offers' in selected_filters:
            filter_query |= Q(has_offers=True)
        
        if filter_query:
            events = events.filter(filter_query)
    
    # Handle single filter parameter (from homepage links)
    single_filter = request.GET.get('filter')
    if single_filter and not selected_filters:  # Only apply if no multiple filters
        if single_filter == 'free':
            events = events.filter(price=0)
        elif single_filter == 'pet-friendly':
            events = events.filter(pet_friendly=True)
        elif single_filter == 'featured':
            events = events.filter(is_featured=True)
        elif single_filter == 'premium':
            events = events.filter(is_premium=True)
        elif single_filter == 'today':
            events = events.filter(date__date=timezone.now().date())
        elif single_filter == 'upcoming':
            week_from_now = timezone.now() + timedelta(days=7)
            events = events.filter(date__lte=week_from_now)
    
    # Sort
    sort = request.GET.get('sort', '-date')
    if sort in ['date', '-date', 'price', '-price', 'title']:
        events = events.order_by(sort)
    
    # Pagination
    paginator = Paginator(events, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if advanced filters are being used
    show_advanced = any([
        date_from, date_to, price_min, price_max, 
        request.GET.get('show_advanced') == 'true'
    ])
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_slug,
        'selected_filters': selected_filters,  # Changed from selected_filter
        'total_events': paginator.count,
        'show_advanced': show_advanced,
        'current_filters': {
            'date_from': date_from,
            'date_to': date_to,
            'price_min': price_min,
            'price_max': price_max,
            'sort': sort,
        }
    }
    
    return render(request, 'event_management/event_list.html', context)


def homepage(request):
    today = timezone.now().date()
    
    context = {
        'featured_events': Event.objects.filter(
            is_featured=True,
            date__gte=today
        ).order_by('date')[:6],
        
        'premium_events': Event.objects.filter(
            is_premium=True,
            date__gte=today
        ).order_by('date')[:6],
        
        'today_events': Event.objects.filter(
            date=today
        ),
    }
    
    for event in context['featured_events']:
        event.is_today = event.date == today
    
    return render(request, 'home.html', context)

def newsletter_signup(request):
    # For now, just redirect to home with a message   
    messages.success(request, "Thanks for your interest! Newsletter coming soon.")
    return redirect('home')

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

def faq_view(request):
    """Display the FAQ page"""
    return render(request, 'faq.html')

def download_ics(request, slug):
    """Generate and download ICS file for the event"""
    event = get_object_or_404(Event, slug=slug, is_active=True)
    
    # Create ICS content
    cal_lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Jersey Events//Event Calendar//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:REQUEST',
        'BEGIN:VEVENT',
        f'UID:{event.id}@jersey.live',
        f'DTSTAMP:{timezone.now().strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{event.date.strftime("%Y%m%dT%H%M%S")}',
    ]
    
    # Add end time (if not set, default to 2 hours after start)
    end_date = event.end_date if hasattr(event, 'end_date') and event.end_date else (event.date + timedelta(hours=2))
    cal_lines.append(f'DTEND:{end_date.strftime("%Y%m%dT%H%M%S")}')
    
    # Add event details - Fix the backslash issue
    description_cleaned = event.description.replace("\n", "\\n")
    location_cleaned = f'{event.venue}, {event.address}'
    
    cal_lines.extend([
        f'SUMMARY:{event.title}',
        f'DESCRIPTION:{description_cleaned}',
        f'LOCATION:{location_cleaned}',
        f'URL:{request.build_absolute_uri(event.get_absolute_url())}',
        'STATUS:CONFIRMED',
        'END:VEVENT',
        'END:VCALENDAR'
    ])
    
    # Create response
    response = HttpResponse('\r\n'.join(cal_lines), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{event.slug}.ics"'
    
    return response


class EventSearchView(ListView):
    model = Event
    template_name = 'events/search_results.html'
    context_object_name = 'events'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        queryset = Event.objects.filter(is_active=True)
        
        if query:
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-rank')
            
        # Add filters
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        # Date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        # Price range
        price_min = self.request.GET.get('price_min')
        price_max = self.request.get('price_max')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
            
        # Sort options
        sort = self.request.GET.get('sort', '-date')
        if sort in ['date', '-date', 'price', '-price', 'title']:
            queryset = queryset.order_by(sort)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.all()
        context['current_filters'] = {
            'category': self.request.GET.get('category'),
            'date_from': self.request.GET.get('date_from'),
            'date_to': self.request.GET.get('date_to'),
            'price_min': self.request.GET.get('price_min'),
            'price_max': self.request.GET.get('price_max'),
            'sort': self.request.GET.get('sort', '-date'),
        }
        return context
    