import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mt5_server"))

import main  # noqa: E402


class MainCTraderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.pending_before = dict(main._ct_oauth_pending)
        self.ct_available_before = main.CT_AVAILABLE
        self.ct_error_before = main.CT_ERROR
        self.poller_before = main._poller_task
        main._ct_oauth_pending.update(
            {"client_id": None, "client_secret": None, "access_token": None}
        )
        main.CT_AVAILABLE = True
        main.CT_ERROR = None
        main._poller_task = None

    def tearDown(self):
        main._ct_oauth_pending.clear()
        main._ct_oauth_pending.update(self.pending_before)
        main.CT_AVAILABLE = self.ct_available_before
        main.CT_ERROR = self.ct_error_before
        main._poller_task = self.poller_before

    def test_ct_authorize_saves_pending_credentials(self):
        req = main.CTAuthorizeRequest(client_id="cid", client_secret="secret")

        with patch.object(main.ct_oauth, "get_auth_url", return_value="https://auth/url") as mocked:
            result = main.ct_authorize(req)

        self.assertEqual(result, {"ok": True, "auth_url": "https://auth/url"})
        self.assertEqual(main._ct_oauth_pending["client_id"], "cid")
        self.assertEqual(main._ct_oauth_pending["client_secret"], "secret")
        self.assertIsNone(main._ct_oauth_pending["access_token"])
        mocked.assert_called_once_with("cid", main._CT_REDIRECT_URI)

    def test_ct_callback_stores_access_token_on_success(self):
        main._ct_oauth_pending["client_id"] = "cid"
        main._ct_oauth_pending["client_secret"] = "secret"

        with patch.object(main.ct_oauth, "exchange_code", return_value=("token-xyz", None)):
            response = main.ct_callback(code="oauth-code")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(main._ct_oauth_pending["access_token"], "token-xyz")

    def test_ct_accounts_list_pre_uses_protobuf_account_loader(self):
        main._ct_oauth_pending.update(
            {"client_id": "cid", "client_secret": "secret", "access_token": "token"}
        )

        with patch.object(
            main.ct_client,
            "get_accounts_by_token",
            return_value=([{"id": 7, "broker": "cTrader", "is_live": False}], None),
        ) as mocked:
            result = main.ct_accounts_list_pre()

        self.assertEqual(
            result,
            {"ok": True, "accounts": [{"id": 7, "broker": "cTrader", "is_live": False}]},
        )
        mocked.assert_called_once_with("token", "cid", "secret")

    async def test_ct_connect_returns_session_payload(self):
        main._ct_oauth_pending.update(
            {"client_id": "cid", "client_secret": "secret", "access_token": "token"}
        )
        fake_loop = SimpleNamespace(run_in_executor=AsyncMock(return_value=(True, None)))

        with patch.object(main.asyncio, "get_event_loop", return_value=fake_loop):
            with patch.object(main, "create_session", return_value="session-1"):
                with patch.object(
                    main.ct_client,
                    "get_snapshot",
                    return_value={"account": {"login": 42, "server": "Demo", "currency": "USD"}},
                ):
                    with patch.object(main.broker_state, "set_broker") as set_broker:
                        result = await main.ct_connect(main.CTConnectRequest(account_id=42, is_live=True))

        self.assertEqual(
            result,
            {
                "ok": True,
                "token": "session-1",
                "name": "42",
                "server": "Demo",
                "currency": "USD",
                "broker": "ctrader",
            },
        )
        set_broker.assert_called_once_with(main.broker_state.BROKER_CT)
        fake_loop.run_in_executor.assert_awaited_once_with(
            None, main.ct_client.connect, "cid", "secret", "token", 42, True
        )

    async def test_ct_connect_rejects_missing_token(self):
        main._ct_oauth_pending.update(
            {"client_id": "cid", "client_secret": "secret", "access_token": None}
        )

        result = await main.ct_connect(main.CTConnectRequest(account_id=42))

        self.assertFalse(result["ok"])
        self.assertIn("No access token", result["error"])


if __name__ == "__main__":
    unittest.main()
