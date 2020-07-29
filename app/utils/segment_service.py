# import analytics
from django.conf import settings
import analytics

class SegmentService:

    def __init__(self, write_key):
        self.analytics = analytics
        analytics.write_key = write_key

    @staticmethod
    def track(user_id, event, properties, **kwargs):
        analytics.track(
            user_id=user_id, 
            event=event,
            properties=properties
        )

    @staticmethod
    def identify(user_id, traits, **kwargs):
        analytics.identify(
            user_id=user_id, 
            traits=traits
        )


segment_service = SegmentService(write_key=settings.SEGMENT_WRITE_KEY)
