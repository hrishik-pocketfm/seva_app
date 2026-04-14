from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    DevoteeRegistrationForm,
    LoginForm,
    SpecialSevaDateForm,
    SevaEventForm,
    UserCreateForm,
    availability_day_fields,
    normalize_phone_number,
    public_form_choice_sets,
    validate_availability_post,
)
from .models import (
    AvailabilitySlot,
    DevoteeRegistration,
    SevaAllocation,
    SevaEvent,
    SpecialSevaDate,
    SpecialSevaSignup,
    User,
)
from .utils import DEFAULT_WHATSAPP_TEMPLATE, PUBLIC_I18N, day_name_from_date, today_local


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


def _slot_matches_event(slot, event):
    if event.seva_location and slot.devotee.seva_location != event.seva_location:
        return False
    if event.start_time and slot.start_time > event.start_time:
        return False
    if event.end_time and slot.end_time < event.end_time:
        return False
    return True


def _devotees_queryset():
    return DevoteeRegistration.objects.prefetch_related(
        Prefetch('availabilities', queryset=AvailabilitySlot.objects.order_by('day_of_week', 'start_time')),
        Prefetch('seva_allocations', queryset=SevaAllocation.objects.select_related('event').order_by('-allocated_at')),
        Prefetch('special_seva_signups', queryset=SpecialSevaSignup.objects.select_related('special_date').order_by('special_date__date')),
    )


def _selected_event(request, selected_date):
    events = list(SevaEvent.objects.filter(date=selected_date).order_by('start_time', 'title'))
    selected_event = None
    raw_id = (request.GET.get('seva') or '').strip()
    if raw_id:
        try:
            selected_event = next((event for event in events if event.pk == int(raw_id)), None)
        except ValueError:
            selected_event = None
    return events, selected_event


def _upcoming_special_dates():
    return SpecialSevaDate.objects.filter(date__gte=today_local()).order_by('date', 'title')


def _build_devotee_cards(devotees, day_index, selected_event):
    cards = []
    for devotee in devotees:
        day_slots = [slot for slot in devotee.availabilities.all() if slot.day_of_week == day_index]
        matching_slots = day_slots
        if selected_event:
            matching_slots = [slot for slot in day_slots if _slot_matches_event(slot, selected_event)]

        allocation = None
        if selected_event:
            allocation = next((item for item in devotee.seva_allocations.all() if item.event_id == selected_event.pk), None)

        devotee.day_slots = day_slots
        devotee.matching_slots = matching_slots
        devotee.is_matching_selected_event = bool(matching_slots)
        devotee.selected_event_allocation = allocation
        cards.append(devotee)
    return cards


def _dashboard_context(request):
    selected_date = _selected_date(request)
    day_index = selected_date.weekday()
    events, selected_event = _selected_event(request, selected_date)
    query = request.GET.get('q', '').strip()

    devotees = _devotees_queryset().order_by('name')
    if query:
        devotees = devotees.filter(
            Q(name__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(address__icontains=query)
        )

    devotees = list(devotees)
    devotee_cards = _build_devotee_cards(devotees, day_index, selected_event)

    if selected_event:
        matching_count = sum(1 for devotee in devotee_cards if devotee.is_matching_selected_event)
        allocated_count = sum(1 for devotee in devotee_cards if devotee.selected_event_allocation)
    else:
        matching_count = sum(1 for devotee in devotee_cards if devotee.day_slots)
        allocated_count = 0

    return {
        'logo_url': LOGO_URL,
        'selected_date': selected_date,
        'selected_day_name': day_name_from_date(selected_date),
        'events': events,
        'selected_event': selected_event,
        'devotees': devotee_cards,
        'query': query,
        'whatsapp_template': DEFAULT_WHATSAPP_TEMPLATE,
        'devotees_count': _devotees_queryset().count(),
        'events_count': len(events),
        'special_dates_count': _upcoming_special_dates().count(),
        'matching_count': matching_count,
        'allocated_count': allocated_count,
    }


def public_registration(request):
    availability_fields = availability_day_fields()
    upcoming_special_dates = list(_upcoming_special_dates())
    valid_special_date_ids = {str(item.pk) for item in upcoming_special_dates}
    selected_special_date_ids = []
    existing = None
    if request.method == 'POST':
        normalized_phone = normalize_phone_number(request.POST.get('phone_number', ''))
        if normalized_phone:
            existing = DevoteeRegistration.objects.filter(phone_number=normalized_phone).first()
        selected_special_date_ids = list(dict.fromkeys([
            value for value in request.POST.getlist('special_dates')
            if value in valid_special_date_ids
        ]))
    form = DevoteeRegistrationForm(request.POST or None, instance=existing)

    if request.method == 'POST':
        try:
            slots = validate_availability_post(request.POST)
        except ValidationError as exc:
            slots = None
            form.add_error(None, exc)

        if form.is_valid() and slots is not None:
            phone_number = normalize_phone_number(form.cleaned_data['phone_number'])
            devotee = existing or DevoteeRegistration(phone_number=phone_number)

            devotee.name = form.cleaned_data['name']
            devotee.phone_number = phone_number
            devotee.initiated = form.cleaned_data['initiated']
            devotee.age = form.cleaned_data['age']
            devotee.gender = form.cleaned_data['gender']
            devotee.address = form.cleaned_data['address']
            devotee.preacher = form.cleaned_data['preacher']
            devotee.seva_location = form.cleaned_data['seva_location']
            devotee.japa_rounds = form.cleaned_data['japa_rounds']
            devotee.connected_since = form.cleaned_data['connected_since']
            devotee.notes = form.cleaned_data['notes']
            devotee.save()

            devotee.availabilities.all().delete()
            for slot in slots:
                AvailabilitySlot.objects.create(
                    devotee=devotee,
                    day_of_week=slot['day_of_week'],
                    start_time=slot['start_time'],
                    end_time=slot['end_time'],
                )

            devotee.special_seva_signups.filter(special_date__date__gte=today_local()).delete()
            SpecialSevaSignup.objects.bulk_create([
                SpecialSevaSignup(devotee=devotee, special_date_id=int(special_date_id))
                for special_date_id in selected_special_date_ids
            ], ignore_conflicts=True)

            if existing:
                messages.success(request, 'आपकी पुरानी जानकारी फोन नंबर से मिल गई। हमने उसे अपडेट कर दिया है।')
            else:
                messages.success(request, 'आपकी सेवा उपलब्धता सफलतापूर्वक सेव हो गई है।')
            return redirect('public_success')

    return render(request, 'core/public_registration.html', {
        'form': form,
        'availability_fields': availability_fields,
        'upcoming_special_dates': upcoming_special_dates,
        'selected_special_date_ids': selected_special_date_ids,
        'logo_url': LOGO_URL,
        'i18n': PUBLIC_I18N,
        **public_form_choice_sets(),
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
    return render(request, 'core/temple_dashboard.html', _dashboard_context(request))


@admin_required
def devotee_list(request):
    return redirect(f"{reverse('temple_dashboard')}?{request.GET.urlencode()}" if request.GET else reverse('temple_dashboard'))


@admin_required
def devotee_detail(request, pk):
    devotee = get_object_or_404(_devotees_queryset(), pk=pk)
    selected_date = _selected_date(request)
    events, selected_event = _selected_event(request, selected_date)
    day_index = selected_date.weekday()
    day_slots = [slot for slot in devotee.availabilities.all() if slot.day_of_week == day_index]
    matching_slots = day_slots if not selected_event else [slot for slot in day_slots if _slot_matches_event(slot, selected_event)]
    current_allocation = None
    if selected_event:
        current_allocation = next((item for item in devotee.seva_allocations.all() if item.event_id == selected_event.pk), None)
    upcoming_special_signups = [item for item in devotee.special_seva_signups.all() if item.special_date.date >= today_local()]
    past_special_signups = [item for item in devotee.special_seva_signups.all() if item.special_date.date < today_local()]

    return render(request, 'core/devotee_detail.html', {
        'logo_url': LOGO_URL,
        'devotee': devotee,
        'selected_date': selected_date,
        'selected_day_name': day_name_from_date(selected_date),
        'events': events,
        'selected_event': selected_event,
        'matching_slots': matching_slots,
        'current_allocation': current_allocation,
        'upcoming_special_signups': upcoming_special_signups,
        'past_special_signups': past_special_signups,
        'whatsapp_template': DEFAULT_WHATSAPP_TEMPLATE,
    })


@admin_required
def allocate_seva(request):
    if request.method != 'POST':
        raise Http404

    devotee = get_object_or_404(_devotees_queryset(), pk=request.POST.get('devotee_id'))
    event = get_object_or_404(SevaEvent, pk=request.POST.get('event_id'))
    has_matching_slot = AvailabilitySlot.objects.filter(devotee=devotee, day_of_week=event.date.weekday()).exists()
    matching_slot = any(_slot_matches_event(slot, event) for slot in devotee.availabilities.filter(day_of_week=event.date.weekday()))

    if not has_matching_slot or not matching_slot:
        messages.error(request, 'यह भक्त चुनी हुई सेवा के समय उपलब्ध नहीं है, इसलिए अभी allocate नहीं किया गया।')
    else:
        allocation, created = SevaAllocation.objects.get_or_create(
            event=event,
            devotee=devotee,
            defaults={'allocated_by': request.user}
        )
        if not created:
            messages.success(request, 'यह सेवा पहले से ही इस भक्त को allocate की हुई है।')
        else:
            messages.success(request, f'{devotee.name} को "{event.display_title}" सेवा allocate कर दी गई है।')

    next_url = request.POST.get('next') or reverse('temple_dashboard')
    return redirect(next_url)


@admin_required
def unallocate_seva(request):
    if request.method != 'POST':
        raise Http404

    devotee = get_object_or_404(_devotees_queryset(), pk=request.POST.get('devotee_id'))
    event = get_object_or_404(SevaEvent, pk=request.POST.get('event_id'))
    SevaAllocation.objects.filter(devotee=devotee, event=event).delete()
    messages.success(request, f'{devotee.name} से "{event.display_title}" सेवा allocation हटा दिया गया है।')
    next_url = request.POST.get('next') or reverse('temple_dashboard')
    return redirect(next_url)


@admin_required
def seva_event_new(request):
    form = SevaEventForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, 'Seva added successfully.')
        return redirect(f"{reverse('temple_dashboard')}?date={event.date.isoformat()}&seva={event.pk}")
    return render(request, 'core/seva_event_form.html', {
        'logo_url': LOGO_URL,
        'form': form,
        'today': today_local().isoformat(),
    })


@admin_required
def special_seva_dates(request):
    form = SpecialSevaDateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        special_date = form.save(commit=False)
        special_date.created_by = request.user
        special_date.save()
        messages.success(request, 'Special seva date added successfully.')
        return redirect('special_seva_dates')

    special_dates = list(
        SpecialSevaDate.objects.prefetch_related(
            Prefetch('signups', queryset=SpecialSevaSignup.objects.select_related('devotee').order_by('devotee__name'))
        ).order_by('date', 'title')
    )
    today = today_local()
    upcoming_dates = [item for item in special_dates if item.date >= today]
    past_dates = [item for item in special_dates if item.date < today]

    return render(request, 'core/special_seva_dates.html', {
        'logo_url': LOGO_URL,
        'form': form,
        'today': today.isoformat(),
        'upcoming_dates': upcoming_dates,
        'past_dates': past_dates,
        'whatsapp_template': DEFAULT_WHATSAPP_TEMPLATE,
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
