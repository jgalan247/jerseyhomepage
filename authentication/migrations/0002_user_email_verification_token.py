# Generated by Django 5.0.2 on 2025-06-19 21:12

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verification_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
