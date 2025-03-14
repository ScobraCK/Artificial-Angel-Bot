class APIError(Exception):
    def __init__(self, message: str, status_code: int = 404):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self):
        return {"error": self.message, "status_code": self.status_code}

class MentemoriError(Exception):
    def __init__(self, response):
        self.response = response
