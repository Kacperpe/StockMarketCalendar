import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mt5_server"))

import ct_oauth  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", json_error=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._json_data


class CtOAuthTests(unittest.TestCase):
    def test_get_auth_url_uses_expected_host_and_query(self):
        url = ct_oauth.get_auth_url("client-123", "http://localhost:8000/callback")

        self.assertIn("https://id.ctrader.com/my/settings/openapi/grantingaccess/", url)
        self.assertIn("client_id=client-123", url)
        self.assertIn("redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback", url)
        self.assertIn("scope=trading", url)
        self.assertIn("response_type=code", url)
        self.assertIn("product=web", url)

    @patch("ct_oauth.requests.get")
    def test_exchange_code_returns_access_token_on_success(self, mock_get):
        mock_get.return_value = FakeResponse(
            status_code=200,
            json_data={"accessToken": "token-abc"},
        )

        token, err = ct_oauth.exchange_code("code-1", "cid", "secret", "http://localhost/callback")

        self.assertEqual(token, "token-abc")
        self.assertIsNone(err)
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["grant_type"], "authorization_code")
        self.assertEqual(kwargs["params"]["code"], "code-1")

    @patch("ct_oauth.requests.get")
    def test_exchange_code_surfaces_json_api_error(self, mock_get):
        mock_get.return_value = FakeResponse(
            status_code=400,
            json_data={"error_description": "bad code"},
        )

        token, err = ct_oauth.exchange_code("bad", "cid", "secret", "http://localhost/callback")

        self.assertIsNone(token)
        self.assertEqual(err, "bad code")

    @patch("ct_oauth.requests.get")
    def test_exchange_code_falls_back_to_http_body_when_response_is_not_json(self, mock_get):
        mock_get.return_value = FakeResponse(
            status_code=405,
            text="Method Not Allowed",
            json_error=ValueError("not json"),
        )

        token, err = ct_oauth.exchange_code("bad", "cid", "secret", "http://localhost/callback")

        self.assertIsNone(token)
        self.assertEqual(err, "HTTP 405: Method Not Allowed")

    @patch("ct_oauth.requests.get")
    def test_list_accounts_maps_rest_payload(self, mock_get):
        mock_get.return_value = FakeResponse(
            status_code=200,
            json_data={
                "data": [
                    {
                        "ctidTraderAccountId": 123,
                        "brokerName": "Pepperstone",
                        "live": True,
                        "depositCurrency": "USD",
                        "balance": 1500,
                    }
                ]
            },
        )

        accounts, err = ct_oauth.list_accounts("access-token")

        self.assertIsNone(err)
        self.assertEqual(
            accounts,
            [
                {
                    "id": 123,
                    "broker": "Pepperstone",
                    "is_live": True,
                    "deposit_currency": "USD",
                    "balance": 1500,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
