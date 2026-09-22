class EdubaoError(Exception):
    """Base for everything raised by the Edubao integration."""

    retryable = False


class EdubaoTransportError(EdubaoError):
    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class EdubaoAPIError(EdubaoError):
    """Edubao answered with a non-2xx status, or `status: false` in the body."""

    def __init__(self, message: str, *, status_code: int, body: object = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.retryable = status_code in (502, 503, 504)


class EdubaoAuthError(EdubaoAPIError):
    """401/403, or we hold no usable token and cannot re-authenticate."""

    def __init__(self, message: str, *, status_code: int = 401, body: object = None):
        super().__init__(message, status_code=status_code, body=body)
