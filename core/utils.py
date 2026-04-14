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


PUBLIC_I18N = {
    'hi': {
        'page_title': 'सेवा पंजीकरण',
        'hero_title': 'सेवा के लिए अपना नाम दें',
        'hero_subtitle': 'अपनी उपलब्धता भर दीजिए। मंदिर की टीम जरूरत होने पर आपसे संपर्क करेगी।',
        'details_title': 'भक्त का विवरण',
        'details_subtitle': 'यह फॉर्म सभी कांग्रिगेशन भक्तों के लिए है। लॉगिन की जरूरत नहीं है।',
        'name': 'नाम',
        'phone': 'फोन नंबर',
        'initiated': 'क्या आप दीक्षित हैं?',
        'age': 'उम्र',
        'gender': 'लिंग',
        'address': 'पता',
        'preacher': 'प्रचारक का नाम',
        'location': 'सेवा का स्थान',
        'japa_rounds': 'रोज कितने राउंड जप करते हैं?',
        'connected_since': 'मंदिर से कब से जुड़े हैं?',
        'notes': 'कोई और जानकारी',
        'special_dates_title': 'विशेष सेवा तिथियां',
        'special_dates_subtitle': 'अगर नीचे कोई विशेष सेवा तिथि दिखाई दे, तो जिन तिथियों पर आप उपलब्ध हों उन्हें चुनें।',
        'availability_title': 'सेवा के लिए उपलब्धता',
        'availability_subtitle': 'जिस दिन सेवा कर सकते हैं, वह दिन चुनें और समय भी भरें।',
        'start_time': 'शुरू समय',
        'end_time': 'समाप्त समय',
        'submit': 'सेवा उपलब्धता भेजें',
        'how_next_title': 'आगे क्या होगा',
        'how_next_1': 'आपकी जानकारी मंदिर की सेवा टीम के पास सेव हो जाएगी।',
        'how_next_2': 'मंदिर के भक्त दिन देखकर देख सकेंगे कि कौन उपलब्ध है।',
        'how_next_3': 'वे आपको सीधे फोन या व्हाट्सऐप कर सकेंगे।',
        'locations_title': 'सेवा स्थान',
        'location_temple': 'मंदिर सेवा: मंदिर परिसर के अंदर की सेवा।',
        'location_outside': 'बाहर सेवा: प्रचार, स्टॉल, यात्रा या बाहर की सेवा।',
        'location_home': 'घर सेवा: घर से की जा सकने वाली सेवा।',
        'toggle_hi': 'हिंदी',
        'toggle_en': 'English',
    },
    'en': {
        'page_title': 'Seva Registration',
        'hero_title': 'Offer Your Seva',
        'hero_subtitle': 'Share your availability and the temple team can contact you when seva is needed.',
        'details_title': 'Devotee Details',
        'details_subtitle': 'This form is for congregation devotees. No login is needed.',
        'name': 'Name',
        'phone': 'Phone Number',
        'initiated': 'Are you initiated?',
        'age': 'Age',
        'gender': 'Gender',
        'address': 'Address',
        'preacher': 'Preacher Name',
        'location': 'Seva Location',
        'japa_rounds': 'How many japa rounds do you chant regularly?',
        'connected_since': 'Since how long are you connected to temple?',
        'notes': 'Additional Notes',
        'special_dates_title': 'Special Seva Dates',
        'special_dates_subtitle': 'If any special seva date is listed below, select the dates on which you are available.',
        'availability_title': 'Availability for Seva',
        'availability_subtitle': 'Select the days you can serve and add your time for each selected day.',
        'start_time': 'Start Time',
        'end_time': 'End Time',
        'submit': 'Submit Seva Availability',
        'how_next_title': 'What Happens Next',
        'how_next_1': 'Your details will be saved for the temple seva team.',
        'how_next_2': 'Temple devotees can filter by date and see who is available.',
        'how_next_3': 'They can call or message you directly on WhatsApp.',
        'locations_title': 'Seva Locations',
        'location_temple': 'Temple Seva: service inside temple premises.',
        'location_outside': 'Outside Seva: outreach, stalls, travel or outdoor support.',
        'location_home': 'Home Seva: seva that can be done from home.',
        'toggle_hi': 'हिंदी',
        'toggle_en': 'English',
    },
}
