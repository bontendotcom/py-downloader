class Authentication:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

class DownloadRequest:
    def __init__(self, url: str, auth: Authentication):
        self.url = url
        self.auth = auth

class DownloadResult:
    def __init__(self, request: DownloadRequest, success: bool, error_message: str = None):
        self.request = request
        self.success = success
        self.error_message = error_message if not success else None

    def __repr__(self):
        return f"<DownloadResult(url={self.request.url}, success={self.success}, error={self.error_message})>"