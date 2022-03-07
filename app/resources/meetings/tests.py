from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from model_bakery.baker import make
from rest_framework.status import HTTP_200_OK

from utils.test_utils import BaseTestCase


class MeetingViewSetTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.meeting = make(
            "Meeting",
            participants=[self.user],
            start=timezone.now() - timedelta(days=1)
        )
        self.second_meeting = make(
            "Meeting",
            participants=[self.user],
            start=timezone.now() - timedelta(days=2))

        self.upcoming_meeting = make(
            "Meeting",
            participants=[self.user],
            start=timezone.now() + timedelta(days=1)
        )
        self.later_upcoming_meeting = make(
            "Meeting",
            participants=[self.user],
            start=timezone.now() + timedelta(days=2)
        )

    def test_past(self):
        response = self.get(reverse("v1:resources:meeting-past"))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["date"], self.meeting.start.date())
        self.assertEqual(response.data[1]["date"], self.second_meeting.start.date())
        self.assertEqual(response.data[1]["meetings"][0]["pk"], self.second_meeting.pk)

    def test_upcoming(self):
        response = self.get(reverse("v1:resources:meeting-upcoming"))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["date"], self.upcoming_meeting.start.date())
        self.assertEqual(response.data[1]["date"], self.later_upcoming_meeting.start.date())
        self.assertEqual(response.data[1]["meetings"][0]["pk"], self.later_upcoming_meeting.pk)
