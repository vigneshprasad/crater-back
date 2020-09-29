import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build

from integrations.google import constants


class GoogleCalendarService:

    SCOPES = constants.CALENDAR_SCOPES
    SERVICE_ACCOUNT_FILE = constants.SERVICE_ACCOUNT_FILE
    GOOGLE_API_VERSION = constants.GOOGLE_API_VERSION
    SERVICE_NAME = constants.CALENDAR_SERVICE_NAME

    def __init__(self, conference_data_version, send_updates, calendar_id):
        self.conference_data_version = conference_data_version
        self.send_updates = send_updates
        self.calendar_id = calendar_id

    def _get_credentials(self):
        """Build credentials for Google API access."""
        initial_credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES
        )
        # Signing the G suite user as hello@worknetwork.in. Every google API will be
        # accessed with the provided account.
        final_credentials = initial_credentials.with_subject(self.calendar_id)
        return final_credentials

    def _build_service(self):
        """Build a google service object. This is used to make any requests to Google."""
        credentials = self._get_credentials()
        service = build(
            self.SERVICE_NAME,
            self.GOOGLE_API_VERSION,
            credentials=credentials
        )
        return service

    def create_event(
            self,
            start_datetime,
            end_datetime,
            users,
            summary=None,
            description=None,

    ):
        request_body = {
            "summary": summary if summary else constants.DEFAULT_SUMMARY_FOR_MEETING_EVENTS,
            "description": description if description else constants.DEFAULT_DESCRIPTION_FOR_MEETING_EVENTS,
            "start": {
                "dateTime": start_datetime.iso_format(),
                "timeZone": constants.DEFAULT_TIMEZONE
            },
            "end": {
                "dateTime": end_datetime.iso_format(),
                "timeZone": constants.DEFAULT_TIMEZONE
            },
            "recurrence": [],
            "attendees": [{"email": user.email for user in users}],
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {
                        "type": constants.HANGOUT_MEET
                    },
                    "requestId": str(uuid.uuid4()),
                }
            }
        }

        service = self._build_service()
        event = service.events().insert(
            calendarId=self.calendar_id,
            body=request_body,
            sendUpdates=self.send_updates,
            conferenceDataVersion=self.conference_data_version
        ).execute()
        print(event)
        hangout_link = event.get('hangoutLink', '')
        return hangout_link

    def update_event(self, event_id, patch_body):
        service = self._build_service()
        event_patch = service.events().patch(
            calendarId=self.calendar_id,
            eventId=event_id,
            body=patch_body,
            conferenceDataVersion=self.conference_data_version
        ).execute()
        return event_patch


google_calendar_service = GoogleCalendarService(
    conference_data_version=constants.CONFERENCE_DATA_VERSION,
    send_updates=constants.SEND_UPDATE_TO_ALL,
    calendar_id=constants.DEFAULT_CALENDAR_ID
)

# sample_data_with_meet_link = {
#     'kind': 'calendar#event',
#     'etag': '"3201802885511000"',
#     'id': 'rvhf3534lg7ltqkpelv97miia4',
#     'status': 'confirmed',
#     'htmlLink': 'https://www.google.com/calendar/event?eid'
#                 '=cnZoZjM1MzRsZzdsdHFrcGVsdjk3bWlpYTQgaGVsbG9Ad29ya25ldHdvcmsuaW4',
#     'created': '2020-09-22T08:56:46.000Z',
#     'updated': '2020-09-25T12:44:38.803Z',
#     'summary': '1:1 WorkNetwork ',
#     'description': '50',
#     'creator': {'email': 'hello@worknetwork.in', 'self': True},
#     'organizer': {'email': 'hello@worknetwork.in', 'self': True},
#     'start': {'dateTime': '2020-09-25T19:00:00+05:30'},
#     'end': {'dateTime': '2020-09-25T19:30:00+05:30'},
#     'iCalUID': 'rvhf3534lg7ltqkpelv97miia4@google.com',
#     'sequence': 1,
#     'attendees': [{'email': 'mayuresh@brainizen.com',
#                    'responseStatus': 'needsAction'},
#                   {'email': 'bhawna.bhatnagar27@gmail.com', 'responseStatus': 'accepted'}],
#     'hangoutLink': 'https://meet.google.com/ybz-dxqy-usz',
#     'conferenceData': {
#         'createRequest': {'requestId': 'aabf9774-1818-4719-ada4-368900e1f3ff',
#                           'conferenceSolutionKey': {'type': 'hangoutsMeet'},
#                           'status': {'statusCode': 'success'}},
#         'entryPoints': [{'entryPointType': 'video',
#                          'uri': 'https://meet.google.com/ybz-dxqy-usz',
#                          'label': 'meet.google.com/ybz-dxqy-usz'},
#                         {'entryPointType': 'more',
#                          'uri': 'https://tel.meet/ybz-dxqy-usz?pin=6344064333790',
#                          'pin': '6344064333790'},
#                         {'regionCode': 'US',
#                          'entryPointType': 'phone',
#                          'uri': 'tel:+1-985-387-5676',
#                          'label': '+1 985-387-5676',
#                          'pin': '227027939'}],
#         'conferenceSolution': {'key': {'type': 'hangoutsMeet'},
#                                'name': 'Google Meet',
#                                'iconUri': 'https://lh5.googleusercontent.com/proxy'
#                                           '/bWvYBOb7O03a7HK5iKNEAPoUNPEXH1CHZjuOkiqxHx8OtyVn9sZ6Ktl8hfqBNQUUbCDg6T2unn'
#                                           'sHx7RSkCyhrKgHcdoosAW8POQJm_ZEvZU9ZfAE7mZIBGr_tDlF8Z_rSzXcjTffVXg3M46v'},
#         'conferenceId': 'ybz-dxqy-usz',
#         'signature': 'ADR/mfMssWaR5ue8YJ9EOaQMVM4g'},
#     'reminders': {'useDefault': False}
# }
