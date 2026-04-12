from datetime import date

from .models import DAY_OF_WEEK_CHOICES

DEFAULT_WHATSAPP_TEMPLATE = """Hare Krishna {name}

You are available for seva on {date} from {time}.

Seva: {seva_title}
Location: {location}
Venue: {venue}

Please let us know if you can join.

ISKCON Bhilai"""


def day_name_from_date(selected_date):
    return dict(DAY_OF_WEEK_CHOICES)[selected_date.weekday()]


def format_event_time(event):
    return f"{event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}"


def today_local():
    return date.today()

