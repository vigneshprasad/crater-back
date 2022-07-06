from base import exceptions as base_exceptions


class CategoryAlreadyFollowed(base_exceptions.BaseAPIException):
    """Thrown when a user tries to follow a category they are already following."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User is already following the category.",
            error_code="categoryAlreadyFollowed"
        )

    def __str__(self):
        return "{}".format(self.message)


class CategoryAlreadyUnfollowed(base_exceptions.BaseAPIException):
    """Thrown when a user tries to unfollow a category they have already unfollowed."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="User has already unfollowed the category.",
            error_code="categoryAlreadyUnFollowed"
        )

    def __str__(self):
        return "{}".format(self.message)
