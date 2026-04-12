from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AvailabilitySlot, DevoteeRegistration, SevaEvent, User


class AvailabilityInline(admin.TabularInline):
    model = AvailabilitySlot
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('name', 'phone_number', 'is_admin', 'is_active')
    search_fields = ('name', 'phone_number')
    ordering = ('name',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'name')}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'is_admin'),
        }),
    )
    list_filter = ('is_admin', 'is_active')
    filter_horizontal = ()


@admin.register(DevoteeRegistration)
class DevoteeRegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'seva_location', 'preacher_name', 'created_at')
    search_fields = ('name', 'phone_number', 'preacher_name')
    list_filter = ('seva_location', 'gender')
    inlines = [AvailabilityInline]


@admin.register(SevaEvent)
class SevaEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'seva_location', 'start_time', 'end_time')
    list_filter = ('seva_location', 'date')
    search_fields = ('title', 'venue', 'description')

