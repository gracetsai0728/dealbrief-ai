class ApiError(Exception):
    def __init__(self, code, message, status_code=400, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
