from django.test import SimpleTestCase

from api.pydantic_models import SessionCreationRequest
from api.utils import clamp_pagination


class SecurityValidationTests(SimpleTestCase):
    def test_session_creation_request_rejects_non_loopback_base_url(self):
        with self.assertRaises(ValueError):
            SessionCreationRequest(base_url="http://example.com:8100")

    def test_clamp_pagination_enforces_bounds(self):
        self.assertEqual(clamp_pagination(page=0, page_size=500), (1, 100))
