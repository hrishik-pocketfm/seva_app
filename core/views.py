from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import (
    DevoteeRegistrationForm,
    LoginForm,
    SevaEventForm,
    UserCreateForm,
    availability_day_fields,
    normalize_phone_number,
    validate_availability_post,
)
from .models import AvailabilitySlot, DevoteeRegistration, SevaEvent, User
from .utils import DEFAULT_WHATSAPP_TEMPLATE, day_name_from_date, format_event_time, today_local


LOGO_URL = 'https://hkmraipur.org/wp-content/uploads/2025/04/HKM-Raipur-Web-Logo-1536-x-921-1.jpg.webp'


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            raise Http404
        return view_func(request, *args, **kwargs)
    return wrapper


def _selected_date(request):
    raw = request.GET.get('date', '').strip()
    if raw:
        try:
            return datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    return today_local()


def _event_matches_slot(event, slot):
    return (
        slot.devotee.seva_location == event.seva_location and
        slot.start_time <= event.start_time and
        slot.end_time >= event.end_time
    )


def _available_devotees_for_date(selected_date):
    day_index = selected_date.weekday()
    slots = list(
        AvailabilitySlot.objects.select_related('devotee')
        .filter(day_of_week=day_index)
        .order_by('start_time', 'devotee__name')
    )
    return day_index, slots


def public_registration(request):
    availability_fields = availability_day_fields()
    if request.method == 'POST':
        form = DevoteeRegistrationForm(request.POST)
        try:
            slots = validate_availability_post(request.POST)
        except ValidationError as exc:
            slots = None
            form.add_error(None, exc)

        if form.is_valid() and slots is not None:
            devotee = form.save(commit=False)
            devotee.phone_number = normalize_phone_number(devotee.phone_number)
            devotee.save()
            for slot in slots:
                AvailabilitySlot.objects.create(
                    devotee=devotee,
                    day_of_week=slot['day_of_week'],
                    start_time=slot['start_time'],
                    end_time=slot['end_time'],
                )
            messages.success(request, 'Your seva availability has been submitted successfully.')
            return redirect('public_success')
    else:
        form = DevoteeRegistrationForm()

    return render(request, 'core/public_registration.html', {
        'form': form,
        'availability_fields': availability_fields,
        'logo_url': LOGO_URL,
    })


def public_success(request):
    return render(request, 'core/public_success.html', {'logo_url': LOGO_URL})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('temple_dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        phone_number = normalize_phone_number(form.cleaned_data['phone_number'])
        user = authenticate(request, phone_number=phone_number)
        if user:
            login(request, user)
            return redirect('temple_dashboard')
        form.add_error('phone_number', 'No temple devotee account found with this phone number.')
    return render(request, 'core/login.html', {'form': form, 'logo_url': LOGO_URL})


def logout_view(request):
    logout(request)
    return redirect('temple_login')


@admin_required
def temple_dashboard(request):
    selected_date = _selected_date(request)
    day_index, available_slots = _available_devotees_for_date(selected_date)
    events = list(SevaEvent.objects.filter(date=selected_date).order_by('start_time', 'title'))

    for event in events:
        event.matching_slots = [slot for slot in available_slots if _event_matches_slot(event, slot)]
        event.time_label = format_event_time(event)

    return render(request, 'core/temple_dashboard.html', {
        'logo_url': LOGO_URL,
        'selected_date': selected_date,
        'selected_day_name': day_name_from_date(selected_date),
        'available_slots': available_slots,
        'events': events,
        'day_index': day_index,
        'whatsapp_template': DEFAULT_WHATSAPP_TEMPLATE,
        'devotees_count': DevoteeRegistration.objects.count(),
        'events_count': SevaEvent.objects.count(),
    })


@admin_required
def devotee_list(request):
    query = request.GET.get('q', '').strip()
    devotees = DevoteeRegistration.objects.prefetch_related(
        Prefetch('availabilities', queryset=AvailabilitySlot.objects.order_by('day_of_week', 'start_time'))
    ).order_by('name')
    if query:
        devotees = devotees.filter(
            Q(name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(preacher_name__icontains=query)
        )
    return render(request, 'core/devotee_list.html', {
        'logo_url': LOGO_URL,
        'devotees': devotees,
        'query': query,
        'whatsapp_template': DEFAULT_WHATSAPP_TEMPLATE,
        'selected_date': today_local(),
    })


@admin_required
def seva_event_new(request):
    form = SevaEventForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, 'Seva added successfully.')
        return redirect(f"{reverse('temple_dashboard')}?date={event.date.isoformat()}")
    return render(request, 'core/seva_event_form.html', {
        'logo_url': LOGO_URL,
        'form': form,
        'today': today_local().isoformat(),
    })


@admin_required
def temple_user_list(request):
    users = User.objects.order_by('name')
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        phone_number = normalize_phone_number(form.cleaned_data['phone_number'])
        if User.objects.filter(phone_number=phone_number).exists():
            form.add_error('phone_number', 'A temple devotee already exists with this phone number.')
        else:
            User.objects.create_user(
                phone_number=phone_number,
                name=form.cleaned_data['name'],
                is_admin=True,
                is_staff=True,
            )
            messages.success(request, 'Temple devotee account created.')
            return redirect('temple_user_list')
    return render(request, 'core/temple_users.html', {
        'logo_url': LOGO_URL,
        'users': users,
        'form': form,
    })
