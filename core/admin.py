from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    AvailabilitySlot,
    DevoteeRegistration,
    SevaAllocation,
    SevaEvent,
    SpecialSevaDate,
    SpecialSevaSignup,
    User,
)


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
    list_display = ('name', 'phone_number', 'seva_location_label', 'preacher', 'japa_rounds', 'created_at')
    search_fields = ('name', 'phone_number', 'preacher', 'connected_since')
    list_filter = ('gender', 'preacher', 'initiated')
    inlines = [AvailabilityInline]


@admin.register(SevaEvent)
class SevaEventAdmin(admin.ModelAdmin):
    list_display = ('display_title', 'day_of_week', 'seva_location', 'start_time', 'end_time')
    list_filter = ('seva_location', 'day_of_week')
    search_fields = ('title', 'venue', 'description')


@admin.register(SevaAllocation)
class SevaAllocationAdmin(admin.ModelAdmin):
    list_display = ('devotee', 'event', 'allocated_by', 'allocated_at')
    list_filter = ('allocated_at', 'event__day_of_week')
    search_fields = ('devotee__name', 'event__title', 'allocated_by__name')


@admin.register(SpecialSevaDate)
class SpecialSevaDateAdmin(admin.ModelAdmin):
    list_display = ('display_title', 'date', 'venue', 'created_by')
    list_filter = ('date',)
    search_fields = ('title', 'venue', 'description')


@admin.register(SpecialSevaSignup)
class SpecialSevaSignupAdmin(admin.ModelAdmin):
    list_display = ('devotee', 'special_date', 'created_at')
    list_filter = ('special_date__date',)
    search_fields = ('devotee__name', 'devotee__phone_number', 'special_date__title')
