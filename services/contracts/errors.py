class AppError(Exception):
    """Application-level error to be handled by FastAPI exception handler."""

    def __init__(self, status_code: int = 400, code: str = "error", message: str = "An error occurred") -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)
