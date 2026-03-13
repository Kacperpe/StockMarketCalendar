import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mt5_server"))

import main  # noqa: E402


class MainMt5Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.poller_before = main._poller_task
        self.ct_available_before = main.CT_AVAILABLE
        self.ct_client_before = main.ct_client
        main._poller_task = None

    def tearDown(self):
        main._poller_task = self.poller_before
        main.CT_AVAILABLE = self.ct_available_before
        main.ct_client = self.ct_client_before

    async def test_auth_connect_sets_mt5_broker_on_success(self):
        req = main.ConnectRequest(login=123, server="Demo-Server", password="secret")
        fake_info = SimpleNamespace(name="Account Name", server="Demo-Server", currency="USD")
        fake_task = SimpleNamespace()

        def _fake_create_task(coro):
            coro.close()
            return fake_task

        with patch.object(main, "connect_dynamic", return_value=True):
            with patch.object(main.broker_state, "set_broker") as mocked_set_broker:
                with patch.object(main, "create_session", return_value="session-token"):
                    with patch.object(main.mt5, "account_info", return_value=fake_info):
                        with patch.object(main, "polling_loop", new_callable=AsyncMock):
                            with patch.object(main.asyncio, "create_task", side_effect=_fake_create_task):
                                main.CT_AVAILABLE = False
                                result = await main.auth_connect(req)

        self.assertTrue(result["ok"])
        self.assertEqual(result["token"], "session-token")
        mocked_set_broker.assert_called_once_with(main.broker_state.BROKER_MT5)


if __name__ == "__main__":
    unittest.main()
