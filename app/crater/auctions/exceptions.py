from base import exceptions as base_exceptions


class BidActionNotAllowed(base_exceptions.BaseAPIException):
    """Thrown when a user who is not a creator for the bid, tries to
        accept or reject bids.

    """

    def __init__(self):
        super().__init__(
            status_code="400",
            message="Action not allowed for this Bid.",
            error_code="bidActionNotAllowed"
        )

    def __str__(self):
        return "{}".format(self.message)
