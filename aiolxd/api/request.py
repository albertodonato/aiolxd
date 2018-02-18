"""Perform requests to the API."""


class Response:
    """An API response."""

    def __init__(self, http_code, http_headers, content):
        self.http_code = http_code
        self.etag = http_headers.get('Etag')
        self.type = content.get('type')
        self.metadata = content.get('metadata', {})


class ResponseError(Exception):
    """An API response error."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(
            'API request failed with {code}: {message}'.format(
                code=self.code, message=self.message))


async def request(session, method, path):
    """Perform an API request with the session."""
    headers = {'Content-Type': 'application/json'}
    response = await session.request(method, path, headers=headers)
    return await _parse_response(response)


async def _parse_response(response):
    """Parse an API reposnse."""
    content = await response.json()
    error_code = content.get('error_code')
    if error_code:
        raise ResponseError(error_code, content.get('error'))

    return Response(response.status, response.headers, content)
