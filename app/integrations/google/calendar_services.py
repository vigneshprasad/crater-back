import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build

from integrations.google import constants


class GoogleCalendarService:

    SCOPES = constants.CALENDAR_SCOPES
    GOOGLE_API_CREDENTIALS = constants.GOOGLE_API_CREDENTIALS
    GOOGLE_API_VERSION = constants.GOOGLE_API_VERSION
    SERVICE_NAME = constants.CALENDAR_SERVICE_NAME

    def __init__(self, conference_data_version, send_updates, calendar_id):
        self.conference_data_version = conference_data_version
        self.send_updates = send_updates
        self.calendar_id = calendar_id
        try:
            self.service = self._build_service()
        except ValueError:
            self.service = None

    def _get_credentials(self):
        """Build credentials for Google API access."""
        initial_credentials = service_account.Credentials.from_service_account_info(
            self.GOOGLE_API_CREDENTIALS,
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

    def get_events(self):
        """Gets all events in the WorkNetwork calendar."""
        if not self.service:
            return None
        return self.service.events().list(
            calendarId=self.calendar_id,
        ).execute()

    def get_event(self, event_id):
        """Gets a specific event from Google calendar API."""
        if not self.service:
            return None
        return self.service.events().get(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()

    def create_event(
            self,
            start_datetime,
            end_datetime,
            users,
            summary=None,
            description=None,
            meeting_link=None

    ):
        """Creates an event on WorkNetwork calendar with a Google meets link.

        Args:
            start_datetime(datetime.datetime): Starting time for the calendar event.
            end_datetime(datetime.datetime): Ending time for the calendar event.
            users(list/queryset): List of user's who are attending the event.
            summary(str): The title of the Google calendar event.
            description(str): The description for Google calendar event.
            meeting_link(str): External meeting link to be added to the event.

        """
        if not self.service:
            return None

        request_id = str(uuid.uuid4())

        # Calculate description based on if we have a meeting link or not.
        summary = summary if summary else constants.DEFAULT_SUMMARY_FOR_MEETING_EVENTS
        description = description if description else constants.DEFAULT_DESCRIPTION_FOR_MEETING_EVENTS

        request_body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": constants.DEFAULT_TIMEZONE
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": constants.DEFAULT_TIMEZONE
            },
            "recurrence": [],
            "attendees": [{"email": user.email} for user in users]
        }

        # Changing the request body based on if we have external meeting link
        # or we are using Google Meets.
        if meeting_link:

            request_body["conferenceData"] = {
                "conferenceSolution": {
                    "name": "1:1 Meeting",
                    "key": {
                        "type": constants.ADD_ON_LINK
                    },
                    # TODO(Nishant): Change this from default Google Meets icon to our icon.
                    "iconUri": "https://fonts.gstatic.com/s/i/productlogos/meet_2020q4/v6/web-512dp/logo_meet_2020q4_color_2x_web_512dp.png"
                },
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "label": meeting_link,
                        "uri": meeting_link
                    }
                ]
            }
        else:
            request_body["conferenceData"] = {
                "createRequest": {
                    "conferenceSolutionKey": {
                        "type": constants.HANGOUT_MEET
                    },
                    "requestId": request_id,
                }
            }

        event = self.service.events().insert(
            calendarId=self.calendar_id,
            body=request_body,
            sendUpdates=self.send_updates,
            conferenceDataVersion=self.conference_data_version
        ).execute()

        hangout_link = meeting_link if meeting_link else event.get('hangoutLink', '')
        event_id = event.get('id', '')

        return event_id, hangout_link

    def update_event(self, event_id, patch_body):
        """Updates an existing event on WorkNetwork Calendar."""
        if not self.service:
            return None

        return self.service.events().patch(
            calendarId=self.calendar_id,
            eventId=event_id,
            body=patch_body,
            conferenceDataVersion=self.conference_data_version
        ).execute()

    def delete_event(self, event_id):
        """Deletes an event from the WorkNetwork calendar."""
        if not self.service:
            return None

        return self.service.events().delete(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()


google_calendar_service = GoogleCalendarService(
    conference_data_version=constants.CONFERENCE_DATA_VERSION,
    send_updates=constants.SEND_UPDATE_TO_ALL,
    calendar_id=constants.DEFAULT_CALENDAR_ID
)
