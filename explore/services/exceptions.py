from rest_framework.exceptions import APIException


class AIDescriptionUnavailable(APIException):
    """Retryable failure to coordinate description generation."""

    status_code = 503
    default_code = 'AI_SERVICE_TEMPORARILY_UNAVAILABLE'
    wait = 5

    def __init__(self):
        super().__init__({
            'code': self.default_code,
            'message': 'Description generation is temporarily unavailable. Please try again shortly.',
        })
