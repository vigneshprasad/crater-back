# import analytics
from django.conf import settings
import analytics

class SegmentService:

    def __init__(self, write_key):
        self.analytics = analytics
        analytics.write_key = write_key

    def track(self, user_id, event, properties, **kwargs):
        analytics.track(
            user_id=user_id, 
            event=event,
            properties=properties
        )

    def identify(self, user_id, traits, **kwargs):
        analytics.identify(
            user_id=user_id, 
            traits=traits
        )

segment_service = SegmentService(write_key=settings.SEGMENT_WRITE_KEY)
