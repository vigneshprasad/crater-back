from django.urls import reverse
from model_bakery.baker import make
from rest_framework.status import HTTP_200_OK

from utils.test_utils import BaseTestCase


class SeriesPublicViewSetTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.meeting = make(
            "Series",
            is_published=True,
            _fill_optional=True,
            make_m2m=True,
            _quantity=2
        )
        make("Series", is_published=False)

    def test_past(self):
        response = self.get(reverse("v1:groups:conversations_series_public-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
