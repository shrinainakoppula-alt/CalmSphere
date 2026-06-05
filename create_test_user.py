import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calmsphere.settings')
django.setup()

from django.contrib.auth.models import User

# Check if testuser exists
user, created = User.objects.get_or_create(username='testuser')
user.set_password('password123')
user.email = 'testuser@example.com'
user.save()

print(f"User testuser created: {created}. Password set to 'password123'.")
