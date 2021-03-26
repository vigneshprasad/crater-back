from rest_framework import status

from base import exceptions as base_exceptions


class GroupMaxSpeakersException(base_exceptions.BaseAPIException):
    """Exception raised when max members reached in group and attempting to add one more
    user

    """

    def __init__(self):
        super().__init__(
            message="This group is full. Please to join another group",
            error_code="groupMaxSpeakersError"
        )

    def __str__(self):
        return f'{self.message}'
