from django.core.management.base import BaseCommand
from django.core.management import CommandError
from django.utils.timezone import localtime, now
from users.models import *


# ========================= BaseCommand =============================

class Command(BaseCommand):
    help = "Creates superusers with frontend user_type"
    
    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Username for the superuser")
        parser.add_argument("--first_name", required=True, help="First name for the superuser")
        parser.add_argument("--last_name", required=True, help="Last name for the superuser")
        parser.add_argument("--email", required=True, help="Email for the superuser")
        parser.add_argument("--password", required=True, help="Password for the superuser")
    
    def handle(self, *args, **options):
        username = options["username"]
        first_name = options["first_name"]
        last_name = options["last_name"]
        email = options["email"]
        password = options["password"]
        
        if CustomUser.objects.filter(username=username).exists():
            raise CommandError(f"User with username '{username}' already exists.")
        
        if CustomUser.objects.filter(email=email).exists():
            raise CommandError(f"User with email '{email}' already exists.")
        
        try:
            front_user = CustomUser.objects.create_superuser(
                username=username,
                first_name=first_name, 
                last_name=last_name,
                email=email,
                password=password,
                user_type="frontend"
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created frontend superuser: {front_user.username}"
                )
            )
            
        except Exception as error:
            raise CommandError(f"Error creating user: {str(error)}")
        
    
# ===================================================================