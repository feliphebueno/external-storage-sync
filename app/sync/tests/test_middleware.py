from unittest import mock

from django.test import override_settings, RequestFactory, TestCase


from app.sync import middleware


class HMacAuthenticationMiddlewareTest(TestCase):
    def setUp(self) -> None:
        self.get_response = mock.Mock()
        self.middleware = middleware.HMacAuthenticationMiddleware(self.get_response)

    def test_call_with_get_request_exempt(self):
        self.get_response.return_value = "mocked_response"
        request = RequestFactory().get("/sync/")

        response = self.middleware(request)

        self.assertEqual(response, "mocked_response")

    def test_call_with_admin_request_exempt(self):
        self.get_response.return_value = "mocked_admin_response"
        request = RequestFactory().get("/admin/sync/")

        response = self.middleware(request)

        self.assertEqual(response, "mocked_admin_response")

    def test_call_with_sync_request_missing_hmac_header(self):
        request = RequestFactory().post("/sync/")

        response = self.middleware(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content, b"""{"detail": "Missing/empty Authorization header"}""")

    def test_call_with_sync_request_invalid_hmac(self):
        request = RequestFactory().post("/sync/", headers={"Authorization": "XYZ"})

        response = self.middleware(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content, b"""{"detail": "Invalid HMAC signature hash"}""")

    @override_settings(SECRET_KEY="mock-test-secret-key")
    def test_call_with_sync_request_valid_hmac(self):
        self.get_response.return_value = "mocked_admin_response"
        mocked_hmac_hex = "ac1a6e75893dd0bbb43621630b909cbec5576f3f1ab692610067c99a620c01cb"
        request = RequestFactory().post("/sync/", headers={"Authorization": mocked_hmac_hex}, data={"mocked": "data"})

        response = self.middleware(request)

        self.assertEqual(response, "mocked_admin_response")


class JSONParseValidationMiddlewareTest(TestCase):
    def setUp(self) -> None:
        self.get_response = mock.Mock()
        self.middleware = middleware.JSONParseValidationMiddleware(self.get_response)

    def test_call_with_get_request_exempt(self):
        self.get_response.return_value = "mocked_response"
        request = RequestFactory().get("/sync/")

        response = self.middleware(request)

        self.assertEqual(response, "mocked_response")

    def test_call_with_admin_request_exempt(self):
        self.get_response.return_value = "mocked_admin_response"
        request = RequestFactory().get("/admin/sync/")

        response = self.middleware(request)

        self.assertEqual(response, "mocked_admin_response")

    def test_call_with_mal_formed_json(self):
        self.get_response.return_value = "mocked_admin_response"
        request = RequestFactory().post("/sync/", data=None)

        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"""{"detail": "Malformed JSON data"}""")

    def test_call_with_invalid_json_data(self):
        self.get_response.return_value = "mocked_admin_response"
        request = RequestFactory().post("/sync/", data={"xyy": True}, content_type="application/json")

        response = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"""{"detail": "Invalid JSON data"}""")

    def test_call_with_valid_json(self):
        self.get_response.return_value = "mocked_admin_response"
        request = RequestFactory().post(
            "/admin/sync/",
            data={
                "oeid": "xyz",
                "ref_id": "mocked",
                "file_name": "787-9.jpg",
                "file_type": "image/jpeg",
            },
        )

        response = self.middleware(request)

        self.assertEqual(response, "mocked_admin_response")
