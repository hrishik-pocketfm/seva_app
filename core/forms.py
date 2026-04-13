from django import forms

from .models import (
    CONNECTED_SINCE_UNIT_CHOICES,
    DAY_OF_WEEK_CHOICES,
    DevoteeRegistration,
    GENDER_CHOICES,
    INITIATED_CHOICES,
    JAPA_ROUND_CHOICES,
    PREACHER_CHOICES,
    SEVA_LOCATION_CHOICES,
    SevaEvent,
    User,
)


class LoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter phone number',
            'class': 'seva-input',
            'autocomplete': 'off',
        })
    )


class DevoteeRegistrationForm(forms.ModelForm):
    preacher = forms.ChoiceField(
        choices=PREACHER_CHOICES,
        widget=forms.Select(attrs={'class': 'seva-input'})
    )

    class Meta:
        model = DevoteeRegistration
        fields = [
            'name', 'phone_number', 'initiated', 'age', 'gender', 'address',
            'preacher', 'seva_location', 'japa_rounds',
            'connected_since_value', 'connected_since_unit', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'seva-input', 'placeholder': 'Full name'}),
            'phone_number': forms.TextInput(attrs={'class': 'seva-input', 'placeholder': 'Phone number', 'inputmode': 'numeric'}),
            'initiated': forms.Select(attrs={'class': 'seva-input'}),
            'age': forms.NumberInput(attrs={'class': 'seva-input', 'placeholder': 'Age', 'min': '1', 'max': '120'}),
            'gender': forms.Select(attrs={'class': 'seva-input'}),
            'address': forms.Textarea(attrs={'class': 'seva-input', 'rows': 3, 'placeholder': 'Full address'}),
            'seva_location': forms.Select(attrs={'class': 'seva-input'}),
            'japa_rounds': forms.Select(attrs={'class': 'seva-input'}),
            'connected_since_value': forms.NumberInput(attrs={'class': 'seva-input', 'placeholder': '1', 'min': '1', 'max': '100'}),
            'connected_since_unit': forms.Select(attrs={'class': 'seva-input'}),
            'notes': forms.Textarea(attrs={'class': 'seva-input', 'rows': 2, 'placeholder': 'Any additional notes'}),
        }


class SevaEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['title', 'description', 'seva_location', 'venue', 'start_time', 'end_time']:
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('title'):
            cleaned_data['title'] = 'Seva'
        return cleaned_data

    class Meta:
        model = SevaEvent
        fields = ['title', 'description', 'seva_location', 'venue', 'date', 'start_time', 'end_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'seva-input', 'placeholder': 'Seva title'}),
            'description': forms.Textarea(attrs={'class': 'seva-input', 'rows': 3, 'placeholder': 'Description'}),
            'seva_location': forms.Select(attrs={'class': 'seva-input'}),
            'venue': forms.TextInput(attrs={'class': 'seva-input', 'placeholder': 'Venue / area'}),
            'date': forms.DateInput(attrs={'class': 'seva-input', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'seva-input', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'seva-input', 'type': 'time'}),
        }


class UserCreateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'seva-input', 'placeholder': 'Temple devotee name'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'seva-input', 'placeholder': 'Phone number'})
    )


def availability_day_fields():
    fields = []
    hindi_labels = {
        'Monday': 'सोमवार',
        'Tuesday': 'मंगलवार',
        'Wednesday': 'बुधवार',
        'Thursday': 'गुरुवार',
        'Friday': 'शुक्रवार',
        'Saturday': 'शनिवार',
        'Sunday': 'रविवार',
    }
    for day_value, day_label in DAY_OF_WEEK_CHOICES:
        slug = day_label.lower()
        fields.append({
            'value': day_value,
            'label': day_label,
            'label_hi': hindi_labels[day_label],
            'label_en': day_label,
            'enabled_name': f'{slug}_enabled',
            'start_name': f'{slug}_start',
            'end_name': f'{slug}_end',
        })
    return fields


def validate_availability_post(post_data):
    cleaned_slots = []
    for day in availability_day_fields():
        if post_data.get(day['enabled_name']) != '1':
            continue
        start = post_data.get(day['start_name'], '').strip()
        end = post_data.get(day['end_name'], '').strip()
        if not start or not end:
            raise forms.ValidationError(f"Please select both start and end time for {day['label']}.")
        cleaned_slots.append({
            'day_of_week': day['value'],
            'start_time': start,
            'end_time': end,
            'label': day['label'],
        })

    if not cleaned_slots:
        raise forms.ValidationError('Please add availability for at least one day.')
    return cleaned_slots


def normalize_phone_number(value):
    return ''.join(ch for ch in value if ch.isdigit())


def public_form_choice_sets():
    return {
        'gender_choices': GENDER_CHOICES,
        'initiated_choices': INITIATED_CHOICES,
        'preacher_choices': PREACHER_CHOICES,
        'seva_location_choices': SEVA_LOCATION_CHOICES,
        'japa_round_choices': JAPA_ROUND_CHOICES,
        'connected_since_unit_choices': CONNECTED_SINCE_UNIT_CHOICES,
    }
