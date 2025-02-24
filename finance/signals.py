from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from rest_framework.authtoken.models import Token
from .models import Period, Category
from django.db.utils import IntegrityError


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def handle_new_user(sender, instance, created, **kwargs):
    """Handles actions when a new user is created."""
    if created:
        try:
            # Create a new period for the user with cycles
            Period.start_new_period(user=instance)

            # Create an authentication token for the user
            Token.objects.get_or_create(user=instance)  # Ensure only one token is created

            # Ensure the default category exists for the user
            Category.objects.get_or_create(
                user=instance,
                code="DEFAULT",
                defaults={
                    "name": "Default",
                    "description": "Default category for reassigned financial records.",
                },
            )
        except IntegrityError:
            # Handle potential database integrity issues (e.g., unique constraints)
            pass
        except Exception:
            # Handle all other exceptions gracefully
            pass
