from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Organizer

class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        
        user = User.objects.get(username='testorganizer')
        print(f"User: {user.username}")
        
        # Try different ways to access organizer
        try:
            org = user.organizer
            print(f"✅ user.organizer: {org.company_name}")
        except Exception as e:
            print(f"❌ user.organizer: {e}")
        
        try:
            org = user.organizer_profile
            print(f"✅ user.organizer_profile: {org.company_name}")
        except Exception as e:
            print(f"❌ user.organizer_profile: {e}")
        
        try:
            org = Organizer.objects.get(user=user)
            print(f"✅ Direct query: {org.company_name}")
        except Exception as e:
            print(f"❌ Direct query: {e}")
