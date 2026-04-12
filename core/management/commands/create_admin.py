from django.core.management.base import BaseCommand

from core.models import User


class Command(BaseCommand):
    help = 'Create a temple devotee admin account'

    def add_arguments(self, parser):
        parser.add_argument('phone_number')
        parser.add_argument('name')

    def handle(self, *args, **options):
        phone_number = ''.join(ch for ch in options['phone_number'] if ch.isdigit())
        name = options['name'].strip()

        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'name': name,
                'is_admin': True,
                'is_staff': True,
                'is_superuser': True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created temple admin {user.name} ({user.phone_number})'))
            return

        user.name = name or user.name
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(update_fields=['name', 'is_admin', 'is_staff', 'is_superuser', 'is_active'])
        self.stdout.write(self.style.WARNING(f'Updated existing temple admin {user.name} ({user.phone_number})'))

