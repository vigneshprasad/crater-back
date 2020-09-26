import pprint

from google.oauth2 import service_account
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = '../../credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)


def build_service():
    initial_credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    final_credentials = initial_credentials.with_subject('hello@worknetwork.in')
    service = googleapiclient.discovery.build(
        'calendar',
        'v3',
        credentials=final_credentials
    )

    return service


google_service = build_service()

body = {
    "summary": "New Meeting Automatic Creation",
    "description": "Meeting Created from backend",
    "start": {
        "dateTime": "2020-09-28T14:30:00",
        "timeZone": "Asia/Kolkata"
    },
    "end": {
        "dateTime": "2020-09-28T15:00:00",
        "timeZone": "Asia/Kolkata"
    },
    "recurrence": [],
    "attendees": [
        {"email": "vignesh@worknetwork.in"},
        {"email": "nishant@worknetwork.in"}
    ],
    "conferenceData": {
        "createRequest": {
            "request_id": "ashdjahbsdqwew",
            "conferenceSolutionKey": {
                "type": "hangoutsMeet"
            }
        },
        "conferenceSolution": {
            "key": {
                "type": "hangoutsMeet"
            }
        }
    }
}

body_patch = {
    "conferenceData": {
        "createRequest": {"request_id": "aabf9774-1818-4719-ada4-368900e1f123"},
        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
    }
}

event = google_service.events().insert(
    calendarId='hello@worknetwork.in',
    body=body,
    conferenceDataVersion=1
).execute()
pprint.pprint(event)

event_patch = google_service.events().patch(
    calendarId='hello@worknetwork.in',
    eventId=event['id'],
    body=body,
    conferenceDataVersion=1
).execute()
pprint.pprint(event_patch)


# ************************************************** #
sample_data_with_meet_link = {
    'kind': 'calendar#event',
    'etag': '"3201802885511000"',
    'id': 'rvhf3534lg7ltqkpelv97miia4',
    'status': 'confirmed',
    'htmlLink': 'https://www.google.com/calendar/event?eid'
                '=cnZoZjM1MzRsZzdsdHFrcGVsdjk3bWlpYTQgaGVsbG9Ad29ya25ldHdvcmsuaW4',
    'created': '2020-09-22T08:56:46.000Z',
    'updated': '2020-09-25T12:44:38.803Z',
    'summary': '1:1 WorkNetwork ',
    'description': '50',
    'creator': {'email': 'hello@worknetwork.in', 'self': True},
    'organizer': {'email': 'hello@worknetwork.in', 'self': True},
    'start': {'dateTime': '2020-09-25T19:00:00+05:30'},
    'end': {'dateTime': '2020-09-25T19:30:00+05:30'},
    'iCalUID': 'rvhf3534lg7ltqkpelv97miia4@google.com',
    'sequence': 1,
    'attendees': [{'email': 'mayuresh@brainizen.com',
                   'responseStatus': 'needsAction'},
                  {'email': 'bhawna.bhatnagar27@gmail.com', 'responseStatus': 'accepted'}],
    'hangoutLink': 'https://meet.google.com/ybz-dxqy-usz',
    'conferenceData': {
        'createRequest': {'requestId': 'aabf9774-1818-4719-ada4-368900e1f3ff',
                          'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                          'status': {'statusCode': 'success'}},
        'entryPoints': [{'entryPointType': 'video',
                         'uri': 'https://meet.google.com/ybz-dxqy-usz',
                         'label': 'meet.google.com/ybz-dxqy-usz'},
                        {'entryPointType': 'more',
                         'uri': 'https://tel.meet/ybz-dxqy-usz?pin=6344064333790',
                         'pin': '6344064333790'},
                        {'regionCode': 'US',
                         'entryPointType': 'phone',
                         'uri': 'tel:+1-985-387-5676',
                         'label': '+1 985-387-5676',
                         'pin': '227027939'}],
        'conferenceSolution': {'key': {'type': 'hangoutsMeet'},
                               'name': 'Google Meet',
                               'iconUri': 'https://lh5.googleusercontent.com/proxy'
                                          '/bWvYBOb7O03a7HK5iKNEAPoUNPEXH1CHZjuOkiqxHx8OtyVn9sZ6Ktl8hfqBNQUUbCDg6T2unn'
                                          'sHx7RSkCyhrKgHcdoosAW8POQJm_ZEvZU9ZfAE7mZIBGr_tDlF8Z_rSzXcjTffVXg3M46v'},
        'conferenceId': 'ybz-dxqy-usz',
        'signature': 'ADR/mfMssWaR5ue8YJ9EOaQMVM4g'},
    'reminders': {'useDefault': False}
}
