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
            summary,
            description,
            conference_name=constants.DEFAULT_CONFERENCE_NAME_FOR_MEETING,
            meeting_link=None

    ):
        """Creates an event on WorkNetwork calendar with a Google meets link.

        Args:
            start_datetime(datetime.datetime): Starting time for the calendar event.
            end_datetime(datetime.datetime): Ending time for the calendar event.
            users(list/queryset): List of user"s who are attending the event.
            summary(str): The title of the Google calendar event.
            description(str): The description for Google calendar event.
            conference_name(str): Conference name for the event.
            meeting_link(str): External meeting link to be added to the event.

        """
        if not self.service:
            return None, meeting_link

        request_id = str(uuid.uuid4())

        if not (start_datetime and end_datetime):
            return None, meeting_link

        # Create Attendees list for the calendar event.
        attendees_list = []
        for user in users:
            if not user.email:
                continue
            attendee_data = {
                "email": user.email,
                "displayName": user.display_name if user.display_name else ""
            }
            attendees_list.append(attendee_data)

        if not attendees_list:
            return None, meeting_link

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
            "attendees": attendees_list
        }

        # Changing the request body based on if we have external meeting link
        # or we are using Google Meets.
        if meeting_link:
            request_body["conferenceData"] = {
                "conferenceSolution": {
                    "name": conference_name,
                    "key": {
                        "type": constants.ADD_ON_LINK
                    },
                    "iconUri": constants.DEFAULT_ICON_URI_FOR_GOOGLE_EVENTS
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

        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=request_body,
                sendUpdates=self.send_updates,
                conferenceDataVersion=self.conference_data_version
            ).execute()
        except Exception as e:
            return None, meeting_link

        hangout_link = meeting_link if meeting_link else event.get("hangoutLink", "")
        event_id = event.get("id", "")

        return event_id, hangout_link

    def update_event_attendees(self, event_id, users):
        """Updates attendees for an existing event on WorkNetwork Calendar.

        Args:
            event_id(str): Event ID for the google calendar event.
            users(list/queryset): All user that are part of the
                updated event.

        """
        if not self.service:
            return None

        # Create Attendees list for the calendar event.
        attendees_list = []
        for user in users:
            if not user.email:
                continue
            attendee_data = {
                "email": user.email,
                "displayName": user.display_name if user.display_name else ""
            }
            attendees_list.append(attendee_data)

        if not attendees_list:
            return None

        patch_body = {
            "attendees": attendees_list
        }

        event = self.service.events().patch(
            calendarId=self.calendar_id,
            eventId=event_id,
            body=patch_body,
            conferenceDataVersion=self.conference_data_version
        ).execute()

        event_id = event.get("id", "")
        return event_id

    def update_event_conference_to_google_meet(self, event_id):
        """Updates conference type to google meets for WorkNetwork Calendar.

        Note:
            We generally use SuperPro links. This is a fallback in case
                superpro is down.
        """
        request_id = str(uuid.uuid4())
        patch_body = {
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {
                        "type": constants.HANGOUT_MEET
                    },
                    "requestId": request_id,
                }
            }
        }
        event = self.service.events().patch(
            calendarId=self.calendar_id,
            eventId=event_id,
            body=patch_body,
            conferenceDataVersion=self.conference_data_version
        ).execute()

        # Return the updated google meet link for the event.
        hangout_link = event.get("hangoutLink", "")

        return hangout_link

    def update_event_to_new_meeting_link(self, event_id, meeting_link):
        """Updates new meeting link in the users WorkNetwork Calendar.

        Args:
            event_id(str): Event ID for the google calendar event.
            meeting_link(str): New meeting link for the calendar.

        """
        patch_body = {
            "conferenceData": {
                "conferenceSolution": {
                    "name": "1:1 Meeting",
                    "key": {
                        "type": constants.ADD_ON_LINK
                    },
                    "iconUri": constants.DEFAULT_ICON_URI_FOR_GOOGLE_EVENTS
                },
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "label": meeting_link,
                        "uri": meeting_link
                    }
                ]
            }
        }

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
            eventId=event_id,
            sendUpdates="all",
        ).execute()


google_calendar_service = GoogleCalendarService(
    conference_data_version=constants.CONFERENCE_DATA_VERSION,
    send_updates=constants.SEND_UPDATE_TO_ALL,
    calendar_id=constants.DEFAULT_CALENDAR_ID
)

google_calendar_service_without_conference_data = GoogleCalendarService(
    conference_data_version=constants.NO_CONFERENCE_DATA_VERSION,
    send_updates=constants.SEND_UPDATE_TO_ALL,
    calendar_id=constants.DEFAULT_CALENDAR_ID
)
