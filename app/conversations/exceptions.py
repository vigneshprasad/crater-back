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


class GroupAlreadyJoined(base_exceptions.BaseAPIException):
    """Exception raised when user has already RSVP'd to the group
        before.

    """

    def __init__(self):
        super().__init__(
            message="You have already joined the group.",
            error_code="groupAlreadyJoined"
        )

    def __str__(self):
        return "{}".format(self.message)


class HostRSVPError(base_exceptions.BaseAPIException):
    """Exception raised when host is trying to RSVP to his own
        stream.

    """

    def __init__(self):
        super().__init__(
            message="You are the host for this group.",
            error_code="hostRSVPError"
        )

    def __str__(self):
        return "{}".format(self.message)


class InvalidParticipantType(base_exceptions.BaseAPIException):
    """Exception raised when we are given Invalid participant type
        to create request API.

    """

    def __init__(self):
        super().__init__(
            message="Participant type provided is invalid.",
            error_code="invalidParticipantType"
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
            error_code="groupCreationError"
        )

    def __str__(self):
        return "{}".format(self.message)


class TopicAlreadySuggested(base_exceptions.BaseAPIException):
    """Exception raised when a user suggests a topic which is already
        suggested.

    """

    def __init__(self):
        super().__init__(
            message="The topic is already suggested.",
            error_code="topicAlreadySuggested"
        )

    def __str__(self):
        return "{}".format(self.message)


class GroupStartDateTimeNotInFuture(base_exceptions.BaseAPIException):
    """Exception raised when a user creates a group with start datetime
        not in future

    """
    def __init__(self):
        super().__init__(
            message="The start datetime is not in the future.",
            error_code="groupStartDateTimeNotInFuture"
        )

    def __str__(self):
        return "{}".format(self.message)


class GroupStartLessThan15minutes(base_exceptions.BaseAPIException):
    """Exception raised when a user creates a group with start datetime
        less then 15 minutes

    """
    def __init__(self):
        super().__init__(
            message="The start time is too soon.",
            error_code="groupStartLessThan15minutes"
        )

    def __str__(self):
        return "{}".format(self.message)


class SeriesAlreadyRSVPed(base_exceptions.BaseAPIException):
    """Exception raised when user has already RSVPed to the series."""

    def __init__(self):
        super().__init__(
            message="You have already RSVPed to the series.",
            error_code="seriesAlreadyRSVPed"
        )

    def __str__(self):
        return "{}".format(self.message)
