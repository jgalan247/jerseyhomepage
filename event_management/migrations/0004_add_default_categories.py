from django.db import migrations
from django.utils.text import slugify

def add_categories(apps, schema_editor):
    Category = apps.get_model('event_management', 'Category')
    
    categories = [
        {'name': 'Things to Do', 'color': '#3B82F6', 'icon': 'calendar'},
        {'name': 'Arts & Culture', 'color': '#EC4899', 'icon': 'palette'},
        {'name': 'Music', 'color': '#8B5CF6', 'icon': 'music'},
        {'name': 'Food and Drink', 'color': '#F59E0B', 'icon': 'utensils'},
        {'name': 'Outdoor Activities', 'color': '#10B981', 'icon': 'tree'},
        {'name': 'Sports', 'color': '#EF4444', 'icon': 'futbol'},
        {'name': 'Mindfulness and Wellbeing', 'color': '#6366F1', 'icon': 'spa'},
    ]
    
    for cat_data in categories:
        Category.objects.get_or_create(
            slug=slugify(cat_data['name']),
            defaults={
                'name': cat_data['name'],
                'color': cat_data['color'],
                'icon': cat_data['icon']
            }
        )

def remove_categories(apps, schema_editor):
    Category = apps.get_model('event_management', 'Category')
    category_names = [
        'Things to Do', 'Arts & Culture', 'Music', 'Food and Drink',
        'Outdoor Activities', 'Sports', 'Mindfulness and Wellbeing'
    ]
    Category.objects.filter(name__in=category_names).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('event_management', '0003_event_has_offers'),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]