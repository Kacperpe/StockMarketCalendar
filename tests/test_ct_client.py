import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mt5_server"))

import ct_client  # noqa: E402


class _PayloadTypeMessage:
    payload_type = None

    def __init__(self):
        self.payloadType = self.payload_type


class ProtoOAApplicationAuthReq:
    def __init__(self):
        self.clientId = None
        self.clientSecret = None


class ProtoOAAccountAuthReq:
    def __init__(self):
        self.ctidTraderAccountId = None
        self.accessToken = None


class ProtoOASymbolsListReq:
    def __init__(self):
        self.ctidTraderAccountId = None
        self.includeArchivedSymbols = None


class ProtoOAReconcileReq(_PayloadTypeMessage):
    payload_type = 104


class ProtoOATraderReq(_PayloadTypeMessage):
    payload_type = 105


class ProtoOASubscribeSpotsReq:
    def __init__(self):
        self.ctidTraderAccountId = None
        self.symbolId = []


class ProtoOASpotEvent(_PayloadTypeMessage):
    payload_type = 106


class ProtoOADealListRes(_PayloadTypeMessage):
    payload_type = 107


class ProtoOAApplicationAuthRes(_PayloadTypeMessage):
    payload_type = 101


class ProtoOAAccountAuthRes(_PayloadTypeMessage):
    payload_type = 102


class ProtoOASymbolsListRes(_PayloadTypeMessage):
    payload_type = 103


class ProtoOAErrorRes(_PayloadTypeMessage):
    payload_type = 199


class ProtoOAGetAccountListByAccessTokenReq:
    def __init__(self):
        self.accessToken = None


class ProtoOAGetAccountListByAccessTokenRes(_PayloadTypeMessage):
    payload_type = 108


class ProtoOACashFlowHistoryListReq:
    def __init__(self):
        self.ctidTraderAccountId = None
        self.fromTimestamp = None
        self.toTimestamp = None


class ProtoOACashFlowHistoryListRes(_PayloadTypeMessage):
    payload_type = 109


def install_fake_ctrader_modules(mode):
    reactor_module = types.ModuleType("twisted.internet")

    class FakeReactor:
        def __init__(self):
            self.called = []

        def callFromThread(self, fn):
            self.called.append(fn)
            fn()

    reactor_module.reactor = FakeReactor()

    pb2_module = types.ModuleType("ctrader_open_api.messages.OpenApiMessages_pb2")
    for name, obj in {
        "ProtoOAApplicationAuthReq": ProtoOAApplicationAuthReq,
        "ProtoOAApplicationAuthRes": ProtoOAApplicationAuthRes,
        "ProtoOAAccountAuthReq": ProtoOAAccountAuthReq,
        "ProtoOAAccountAuthRes": ProtoOAAccountAuthRes,
        "ProtoOASymbolsListReq": ProtoOASymbolsListReq,
        "ProtoOASymbolsListRes": ProtoOASymbolsListRes,
        "ProtoOAReconcileReq": ProtoOAReconcileReq,
        "ProtoOAReconcileRes": ProtoOAReconcileReq,
        "ProtoOATraderReq": ProtoOATraderReq,
        "ProtoOATraderRes": ProtoOATraderReq,
        "ProtoOASubscribeSpotsReq": ProtoOASubscribeSpotsReq,
        "ProtoOASpotEvent": ProtoOASpotEvent,
        "ProtoOADealListRes": ProtoOADealListRes,
        "ProtoOAErrorRes": ProtoOAErrorRes,
        "ProtoOAGetAccountListByAccessTokenReq": ProtoOAGetAccountListByAccessTokenReq,
        "ProtoOAGetAccountListByAccessTokenRes": ProtoOAGetAccountListByAccessTokenRes,
        "ProtoOACashFlowHistoryListReq": ProtoOACashFlowHistoryListReq,
        "ProtoOACashFlowHistoryListRes": ProtoOACashFlowHistoryListRes,
    }.items():
        setattr(pb2_module, name, obj)

    ctrader_module = types.ModuleType("ctrader_open_api")

    class FakeClient:
        def __init__(self, host, port, protocol):
            self.host = host
            self.port = port
            self.protocol = protocol
            self.connected_callback = None
            self.disconnected_callback = None
            self.callbacks = {}
            self.stopped = False

        def setConnectedCallback(self, cb):
            self.connected_callback = cb

        def setDisconnectedCallback(self, cb):
            self.disconnected_callback = cb

        def setMessageReceivedCallbacks(self, callbacks):
            self.callbacks = callbacks

        def startService(self):
            self.connected_callback(self)

        def stopService(self):
            self.stopped = True

        def send(self, req, clientMsgId=None):
            if isinstance(req, ProtoOAApplicationAuthReq):
                if mode in {"connect_error", "accounts_error"}:
                    error = types.SimpleNamespace(description="bad token")
                    self.callbacks[ProtoOAErrorRes().payloadType](self, error)
                    return
                self.callbacks[ProtoOAApplicationAuthRes().payloadType](self, types.SimpleNamespace())
                return

            if isinstance(req, ProtoOAAccountAuthReq):
                self.callbacks[ProtoOAAccountAuthRes().payloadType](self, types.SimpleNamespace())
                return

            if isinstance(req, ProtoOASymbolsListReq):
                payload = types.SimpleNamespace(
                    symbol=[types.SimpleNamespace(symbolId=1, symbolName="EURUSD")]
                )
                self.callbacks[ProtoOASymbolsListRes().payloadType](self, payload)
                return

            if isinstance(req, ProtoOAGetAccountListByAccessTokenReq):
                payload = types.SimpleNamespace(
                    ctidTraderAccount=[
                        types.SimpleNamespace(
                            ctidTraderAccountId=12345,
                            isLive=True,
                            traderLogin=777,
                        )
                    ]
                )
                self.callbacks[ProtoOAGetAccountListByAccessTokenRes().payloadType](self, payload)
                return

            if isinstance(req, ProtoOACashFlowHistoryListReq):
                payload = types.SimpleNamespace(depositWithdraw=[])
                self.callbacks[ProtoOACashFlowHistoryListRes().payloadType](self, payload)

    ctrader_module.Client = FakeClient
    ctrader_module.TcpProtocol = object()
    ctrader_module.EndPoints = types.SimpleNamespace(PROTRADE_HOST="demo", PROTRADE_PORT=5035)
    ctrader_module.Protobuf = types.SimpleNamespace(extract=lambda message: message)

    return {
        "twisted.internet": reactor_module,
        "ctrader_open_api": ctrader_module,
        "ctrader_open_api.messages.OpenApiMessages_pb2": pb2_module,
    }


class CtClientTests(unittest.TestCase):
    def setUp(self):
        ct_client._client = None
        ct_client._connected = False
        ct_client._error = None
        ct_client._account_id = None
        ct_client._symbol_map.clear()

    def test_resolve_protobuf_endpoint_prefers_live_or_demo_by_flag(self):
        endpoints = types.SimpleNamespace(
            PROTOBUF_LIVE_HOST="live.host",
            PROTOBUF_DEMO_HOST="demo.host",
            PROTOBUF_PORT=5035,
        )

        live_host, live_port = ct_client._resolve_protobuf_endpoint(endpoints, is_live=True)
        demo_host, demo_port = ct_client._resolve_protobuf_endpoint(endpoints, is_live=False)

        self.assertEqual((live_host, live_port), ("live.host", 5035))
        self.assertEqual((demo_host, demo_port), ("demo.host", 5035))

    def test_get_accounts_by_token_returns_mapped_accounts(self):
        fake_modules = install_fake_ctrader_modules("accounts_success")

        with patch.dict(sys.modules, fake_modules, clear=False):
            with patch.object(ct_client, "_ensure_reactor", return_value=None):
                accounts, err = ct_client.get_accounts_by_token("token", "cid", "secret")

        self.assertIsNone(err)
        self.assertEqual(
            accounts,
            [
                {
                    "id": 12345,
                    "broker": "cTrader",
                    "is_live": True,
                    "trader_login": 777,
                }
            ],
        )

    def test_get_accounts_by_token_returns_error_from_proto_callback(self):
        fake_modules = install_fake_ctrader_modules("accounts_error")

        with patch.dict(sys.modules, fake_modules, clear=False):
            with patch.object(ct_client, "_ensure_reactor", return_value=None):
                accounts, err = ct_client.get_accounts_by_token("token", "cid", "secret")

        self.assertEqual(accounts, [])
        self.assertEqual(err, "bad token")

    def test_connect_returns_success_after_auth_chain(self):
        fake_modules = install_fake_ctrader_modules("connect_success")

        with patch.dict(sys.modules, fake_modules, clear=False):
            with patch.object(ct_client, "_ensure_reactor", return_value=None):
                with patch.object(ct_client, "_schedule_poll", return_value=None):
                    ok, err = ct_client.connect("cid", "secret", "token", 12345)

        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(ct_client._connected)
        self.assertEqual(ct_client._account_id, 12345)
        self.assertEqual(ct_client._symbol_map[1], "EURUSD")

    def test_connect_returns_error_when_proto_error_arrives(self):
        fake_modules = install_fake_ctrader_modules("connect_error")

        with patch.dict(sys.modules, fake_modules, clear=False):
            with patch.object(ct_client, "_ensure_reactor", return_value=None):
                ok, err = ct_client.connect("cid", "secret", "token", 12345)

        self.assertFalse(ok)
        self.assertEqual(err, "bad token")


if __name__ == "__main__":
    unittest.main()
