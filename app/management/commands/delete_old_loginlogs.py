from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import LoginLog  # Replace with your app name

class Command(BaseCommand):
    help = 'Deletes LoginLog entries older than 18 hours'

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(hours=18)
        deleted, _ = LoginLog.objects.filter(login_time__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted} old LoginLog records older than 18 hours."))
