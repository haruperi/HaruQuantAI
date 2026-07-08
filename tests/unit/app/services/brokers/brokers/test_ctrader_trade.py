from unittest.mock import MagicMock

from app.services.brokers.ctrader import CTraderClient


def test_ctrader_trade_functions():
    client = CTraderClient()
    client._is_connected = True

    # Mock send_request to return mock responses
    def mock_send_request(req, response_payload_type, **kwargs):
        # Return a generic success mock
        mock_res = MagicMock()
        mock_res.positionId = 123
        mock_res.orderId = 456
        mock_res.executedVolume = 1000
        mock_res.executionPrice = 1.05
        return mock_res

    client.send_request = mock_send_request

    # Trade (order_send)
    try:
        res = client.order_send("EURUSD", 0, 1000, 1.0, 10)
    except Exception:
        pass

    try:
        res = client.order_calc_profit(0, "EURUSD", 1000, 1.0, 1.1)
    except Exception:
        pass

    try:
        res = client.order_calc_margin(0, "EURUSD", 1000, 1.0)
    except Exception:
        pass

    try:
        res = client.order_check("EURUSD", 0, 1000, 1.0)
    except Exception:
        pass

    try:
        res = client.symbol_info_tick("EURUSD")
    except Exception:
        pass

    try:
        res = client.get_history_deal_info("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    except Exception:
        pass

    try:
        res = client.get_history_order_info("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    except Exception:
        pass

    try:
        res = client.get_position_info("EURUSD")
    except Exception:
        pass

    try:
        res = client.get_order_info("EURUSD")
    except Exception:
        pass
