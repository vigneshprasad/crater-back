from base import exceptions as base_exceptions


class LoginOtpMismatch(base_exceptions.BaseAPIException):
    """When a user's Login OTP doesn't match."""

    def __init__(self):
        super().__init__(
            status_code="400",
            message="Wrong OTP provided.",
            error_code="loginOtpMismatch"
        )

    def __str__(self):
        return "{}".format(self.message)


class NoUsernameProvided(base_exceptions.BaseAPIException):
    """While login if not username is provided."""

    def __init__(self):
        super().__init__(
            message="Please provide a valid phone number.",
            error_code="noUsernameProvided"
        )

    def __str__(self):
        return "{}".format(self.message)


class UserDoesNotExistForUsername(base_exceptions.BaseAPIException):
    """Exception thrown when a user does not exist for a given username."""

    def __init__(self):
        super().__init__(
            message="No user is registered with this phone number.",
            error_code="userDoesNotExistForUsername"
        )

    def __str__(self):
        return "{}".format(self.message)
