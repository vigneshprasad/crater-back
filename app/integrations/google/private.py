from django.utils import timezone

from integrations.google import constants
from integrations.google import models
from integrations.google.calendar_services import google_calendar_service


def get_and_update_response_status_for_user(user):

    google_calendar_event = models.GoogleCalendarEvent.objects.filter(
        user=user,
        ends_at__gt=timezone.now(),
    ).last()

    # If there is no calendar event in the future, return.
    if not google_calendar_event:
        return

    # If the calendar status is already in accepted status, don't do anything.
    if google_calendar_event.status in constants.ACCEPTED_CALENDAR_STATUSES:
        return google_calendar_event.status

    event_id = google_calendar_event.event_id
    event_data = google_calendar_service.get_event(event_id)
    attendees = event_data.get('attendees')
    if not attendees:
        return

    # Default status.
    status = constants.CALENDAR_RESPONSE_STATUSES[0][0]

    for attendee in attendees:
        if attendee.get('email') == user.email:
            status = attendee.get('responseStatus')

    # Update status in the model with the latest status.
    google_calendar_event.status = status
    google_calendar_event.save()

    return status

# {'kind': 'calendar#event',
#    'etag': '"3203943547331000"',
#    'id': 'kp47g8v3btooe5de59hpkhhqtc',
#    'status': 'confirmed',
#    'htmlLink': 'https://www.google.com/calendar/event?eid=a3A0N2c4djNidG9vZTVkZTU5aHBraGhxdGMgaGVsbG9Ad29ya25ldHdvcmsuaW4',
#    'created': '2020-10-06T06:47:29.000Z',
#    'updated': '2020-10-06T09:31:37.935Z',
#    'summary': '1:1 WorkNetwork ',
#    'description': 'Hi, please check your email ID for an introduction to your match. If you need to reschdule please reply on the thread created. Please join the meeting with the email ID above. If not a google ID you may have some trouble loggining in; in which case please email on the thread. 501',
#    'creator': {'email': 'hello@worknetwork.in', 'self': True},
#    'organizer': {'email': 'hello@worknetwork.in', 'self': True},
#    'start': {'dateTime': '2020-10-08T14:00:00+05:30'},
#    'end': {'dateTime': '2020-10-08T14:30:00+05:30'},
#    'iCalUID': 'kp47g8v3btooe5de59hpkhhqtc@google.com',
#    'sequence': 0,
#    'attendees': [{'email': 'chintan@pixelandlens.com',
#      'responseStatus': 'accepted'},
#     {'email': 'gtmtiwari@gmail.com', 'responseStatus': 'accepted'}],
#    'hangoutLink': 'https://meet.google.com/cuk-tuhi-nag',
#    'conferenceData': {'createRequest': {'requestId': '8ffcdb6e-6fd0-4e77-9891-95427eb988cf',
#      'conferenceSolutionKey': {'type': 'hangoutsMeet'},
#      'status': {'statusCode': 'success'}},
#     'entryPoints': [{'entryPointType': 'video',
#       'uri': 'https://meet.google.com/cuk-tuhi-nag',
#       'label': 'meet.google.com/cuk-tuhi-nag'},
#      {'entryPointType': 'more',
#       'uri': 'https://tel.meet/cuk-tuhi-nag?pin=5798160768219',
#       'pin': '5798160768219'},
#      {'regionCode': 'US',
#       'entryPointType': 'phone',
#       'uri': 'tel:+1-347-574-9160',
#       'label': '+1 347-574-9160',
#       'pin': '235391317'}],
#     'conferenceSolution': {'key': {'type': 'hangoutsMeet'},
#      'name': 'Google Meet',
#      'iconUri': 'https://fonts.gstatic.com/s/i/productlogos/meet_2020q4/v6/web-512dp/logo_meet_2020q4_color_2x_web_512dp.png'},
#     'conferenceId': 'cuk-tuhi-nag',
#     'signature': 'AGkP/s0EK+bNyrk7JI67TrQpxmJd'},
#    'reminders': {'useDefault': False}}]}