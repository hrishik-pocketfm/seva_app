from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

SEVA_LOCATION_CHOICES = [
    ('TEMPLE', 'Temple Seva'),
    ('OUTSIDE', 'Outside Seva'),
    ('HOME', 'Home Seva'),
]

DAY_OF_WEEK_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]


class UserManager(BaseUserManager):
    def create_user(self, phone_number, name, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        user = self.model(phone_number=phone_number, name=name, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number=phone_number, name=name, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15, unique=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return f'{self.name} ({self.phone_number})'


class DevoteeRegistration(models.Model):
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    preacher_name = models.CharField(max_length=150)
    seva_location = models.CharField(max_length=10, choices=SEVA_LOCATION_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def wa_number(self):
        digits = ''.join(c for c in self.phone_number if c.isdigit())
        if len(digits) == 10:
            return '91' + digits
        if len(digits) == 11 and digits.startswith('0'):
            return '91' + digits[1:]
        if len(digits) == 12 and digits.startswith('91'):
            return digits
        return '91' + digits[-10:] if len(digits) >= 10 else digits


class AvailabilitySlot(models.Model):
    devotee = models.ForeignKey(
        DevoteeRegistration,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = [('devotee', 'day_of_week')]

    def __str__(self):
        return f'{self.devotee.name} - {self.get_day_of_week_display()}'


class SevaEvent(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    seva_location = models.CharField(max_length=10, choices=SEVA_LOCATION_CHOICES)
    venue = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='seva_events_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time', 'title']

    def __str__(self):
        return f'{self.title} - {self.date}'

