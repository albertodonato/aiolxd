from pathlib import Path
from textwrap import dedent
from unittest import TestCase

from toolrack.testing import TempDirFixture
from toolrack.testing.async import LoopTestCase

from ..http import (
    request,
    Response,
    ResponseError,
)
from ..testing import (
    FakeSession,
    make_error_response,
    make_sync_response,
)


class RequestTests(LoopTestCase):

    def setUp(self):
        super().setUp()
        self.tempdir = self.useFixture(TempDirFixture())
        self.session = FakeSession()

    async def test_request(self):
        """The request call makes an HTTP request and returns a Response."""
        response = make_sync_response(metadata=['/1.0'])
        self.session.responses.append(response)
        resp = await request(self.session, 'GET', '/')
        self.assertEqual(resp.http_code, 200)
        self.assertEqual(resp.metadata, ['/1.0'])
        self.assertEqual(
            self.session.calls,
            [('GET', '/', None, {}, None)])

    async def test_request_with_content(self):
        """The request call can include content in the request."""
        response = make_sync_response(metadata=['response'])
        self.session.responses.append(response)
        content = {'some': 'content'}
        await request(self.session, 'POST', '/', content=content)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None,
              {'Content-Type': 'application/json'},
              content)])

    async def test_request_with_upload_path(self):
        """The request call can include content from a file."""
        upload_file = Path(self.tempdir.mkfile(content='data'))
        response = make_sync_response(metadata=['response'])
        self.session.responses.append(response)
        await request(self.session, 'POST', '/', upload=upload_file)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None,
              {'Content-Type': 'application/octet-stream'}, 'data')])

    async def test_request_with_upload_file_descriptor(self):
        """The request call can include content from a file descriptor."""
        upload_file = Path(self.tempdir.mkfile(content='data'))
        response = make_sync_response(metadata=['response'])
        self.session.responses.append(response)
        upload = upload_file.open()
        await request(self.session, 'POST', '/', upload=upload)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None,
              {'Content-Type': 'application/octet-stream'}, 'data')])
        # the passed file descriptor is closed
        self.assertTrue(upload.closed)

    async def test_request_with_params(self):
        """The request call can include params in the request."""
        response = make_sync_response(metadata=['response'])
        self.session.responses.append(response)
        params = {'a': 'param'}
        await request(self.session, 'POST', '/', params=params)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', params, {}, None)])

    async def test_request_with_headers(self):
        """The request call can include extra headers in the request."""
        response = make_sync_response(metadata=['response'])
        self.session.responses.append(response)
        headers = {'X-Sample': 'value'}
        await request(self.session, 'POST', '/', headers=headers)
        self.assertEqual(
            self.session.calls,
            [('POST', '/', None, {'X-Sample': 'value'}, None)])

    async def test_request_error(self):
        """The request call raises an error on failed requests."""
        response = make_error_response(error='Something went wrong')
        self.session.responses.append(response)
        with self.assertRaises(ResponseError) as cm:
            await request(self.session, 'GET', '/'),
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.message, 'Something went wrong')
        self.assertEqual(
            str(cm.exception),
            'API request failed with 400: Something went wrong')


class ResponseTests(TestCase):

    def test_instantiate(self):
        """A Response can be instantiated."""
        headers = {'ETag': 'abcde'}
        content = {
            'type': 'sync',
            'metadata': {'some': 'content'}}
        response = Response(200, headers, content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.etag, 'abcde')
        self.assertEqual(response.type, 'sync')
        self.assertEqual(response.metadata, {'some': 'content'})

    def test_pprint(self):
        """The pprint method pretty-prints the response."""
        headers = {'ETag': 'abcde', 'Location': '/some/url'}
        content = {
            'type': 'sync',
            'metadata': {'some': 'content'}}
        response = Response(200, headers, content)
        self.assertEqual(
            dedent("""\
            {'etag': 'abcde',
             'http-code': 200,
             'location': '/some/url',
             'metadata': {'some': 'content'},
             'type': 'sync'}"""),
            response.pprint())