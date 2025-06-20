from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix duplicate email verification tokens'

    def handle(self, *args, **options):
        # Find all users with duplicate tokens
        self.stdout.write('Checking for duplicate tokens...')
        
        # Get all tokens and count occurrences
        token_counts = {}
        users = User.objects.all()
        
        for user in users:
            token = str(user.email_verification_token)
            if token not in token_counts:
                token_counts[token] = []
            token_counts[token].append(user)
        
        # Fix duplicates
        fixed_count = 0
        for token, users_list in token_counts.items():
            if len(users_list) > 1:
                self.stdout.write(f'\nFound {len(users_list)} users with token: {token}')
                # Keep the first user's token, regenerate for others
                for user in users_list[1:]:
                    new_token = uuid.uuid4()
                    user.email_verification_token = new_token
                    user.save()
                    self.stdout.write(f'  - Fixed user {user.email} with new token: {new_token}')
                    fixed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Fixed {fixed_count} duplicate tokens'))
        
        # Show current status
        self.stdout.write('\nCurrent token status:')
        unique_tokens = User.objects.values_list('email_verification_token', flat=True).distinct()
        total_users = User.objects.count()
        self.stdout.write(f'  Total users: {total_users}')
        self.stdout.write(f'  Unique tokens: {len(unique_tokens)}')
