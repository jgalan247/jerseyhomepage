from django.contrib import admin
from .models import Category, Event, EventImage

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'venue', 'price', 'is_featured', 'is_active')
    list_filter = ('category', 'is_featured', 'is_active', 'date')
    search_fields = ('title', 'description', 'venue')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventImageInline]
    date_hierarchy = 'date'
