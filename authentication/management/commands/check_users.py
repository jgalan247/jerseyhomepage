from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        
        print("=== USER MODEL FIELDS ===")
        for field in User._meta.fields:
            print(f"  {field.name}: {field.__class__.__name__}")
        
        print("\n=== CHECKING TEST USERS ===")
        try:
            user = User.objects.get(username='testbuyer')
            print(f"testbuyer exists: {user.email}")
            print(f"  is_active: {user.is_active}")
            for field in User._meta.fields:
                if 'email' in field.name.lower() or 'verif' in field.name.lower():
                    print(f"  {field.name}: {getattr(user, field.name, 'N/A')}")
        except Exception as e:
            print(f"testbuyer error: {e}")
