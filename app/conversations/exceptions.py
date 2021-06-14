from rest_framework import status

from base import exceptions as base_exceptions


class GroupMaxSpeakersException(base_exceptions.BaseAPIException):
    """Exception raised when max members reached in group and attempting to add one more
        user.

    """

    def __init__(self):
        super().__init__(
            message="This group is full. Please to join another group",
            error_code="groupMaxSpeakersError"
        )

    def __str__(self):
        return "{}".format(self.message)


class GroupJoinedAtTheSameTime(base_exceptions.BaseAPIException):
    """Exception raised when a user tries to join groups happening at the
        same time.

    """

    def __init__(self):
        super().__init__(
            message="You have a conversation at the same time. Try to join conversation at different time.",
            # TODO(Abhishek): Change this to groupJoinedAtTheSameTime once app push handle multiple error codes.
            error_code="groupMaxSpeakersError"
        )

    def __str__(self):
        return "{}".format(self.message)


class GroupCreatedAtTheSameTime(base_exceptions.BaseAPIException):
    """Exception raised when a user tries to create group at the same
        time as his scheduled groups.

    """

    def __init__(self):
        super().__init__(
            message="You already have a conversation at the same time. Please select a different time",
            # TODO(Abhishek): Change this to groupJoinedAtTheSameTime once app push handle multiple error codes.
            error_code="groupCreationError"
        )

    def __str__(self):
        return "{}".format(self.message)
