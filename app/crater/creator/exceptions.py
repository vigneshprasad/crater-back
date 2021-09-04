from base import exceptions as base_exceptions


class UserNotFollowingCreator(base_exceptions.BaseAPIException):
    """Thrown when a user tries to unfollow a creator he has never
        followed.

    """

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User does not followed the provided creator.",
            error_code="userNotFollowingCreator"
        )

    def __str__(self):
        return "{}".format(self.message)


class CreatorAlreadyFollowed(base_exceptions.BaseAPIException):
    """Thrown when a user tries to follow a creator they are already following."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User is already following the creator.",
            error_code="creatorAlreadyFollowed"
        )

    def __str__(self):
        return "{}".format(self.message)


class CreatorAlreadyUnFollowed(base_exceptions.BaseAPIException):
    """Thrown when a user tries to unfollow a creator they have already unfollowed."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User has already unfollowed the creator.",
            error_code="creatorAlreadyUnFollowed"
        )

    def __str__(self):
        return "{}".format(self.message)


class CommunityAlreadyJoined(base_exceptions.BaseAPIException):
    """Thrown when a user tries to unfollow a creator they have already unfollowed."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User is already part of the community.",
            error_code="communityAlreadyJoined"
        )

    def __str__(self):
        return "{}".format(self.message)


class CommunityAlreadyLeft(base_exceptions.BaseAPIException):
    """Thrown when a user tries to unfollow a creator they have already unfollowed."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User has already left the community.",
            error_code="communityAlreadyLeft"
        )

    def __str__(self):
        return "{}".format(self.message)
