from rest_framework import status


class BaseAPIException(Exception):
    """Base Exception for Api View Responses

    Attributes:
        message: explanation of the error
        error_code(string): string error Code for Exception
        status_code: status code for error
    """

    def __init__(self, message, error_code, status_code=status.HTTP_400_BAD_REQUEST):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        super(BaseAPIException, self).__init__(self.message)

    def __str__(self):
        return f'{self.message}'

    def get_error_body(self):
        return {
            'error_code': self.error_code,
            'error_message': self.message,
        }


