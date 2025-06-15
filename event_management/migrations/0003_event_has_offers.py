from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('event_management', '0002_event_search_vector_alter_event_organizer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='has_offers',
            field=models.BooleanField(default=False),
        ),
    ]