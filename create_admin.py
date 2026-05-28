import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esg_core.settings')
django.setup()

from django.contrib.auth.models import User
from esg_pipeline.models import Organization

def seed_production():
    username = "admin"
    email = "admin@test.com"
    password = "BreatheESG2026!" # Change this to whatever secure password you want
    
    # 1. Create Superuser if it doesn't exist
    if not User.objects.filter(username=username).exists():
        print("Creating production superuser account...")
        User.objects.create_superuser(username, email, password)
    else:
        print("Superuser profile already exists.")

    # 2. Create the Tenant Organization if it doesn't exist
    if not Organization.objects.filter(name="Breathe ESG Test Corp").exists():
        print("Creating production corporate tenant...")
        Organization.objects.create(name="Breathe ESG Test Corp")
    else:
        print("Tenant Organization already exists.")

if __name__ == "__main__":
    seed_production()