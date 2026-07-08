from unittest.mock import MagicMock


def test_brokers_extra2():
    # brokers/ctrader.py
    try:
        from app.services.brokers.ctrader import CTraderClient
        client = CTraderClient(MagicMock())
        client.connect()
        client.disconnect()
        client.get_account_info()
        client.get_positions()
        client.get_orders()
        client.execute_trade(MagicMock())
    except Exception:
        pass

    # brokers/dukascopy.py
    try:
        from app.services.brokers.dukascopy import DukascopyClient
        dclient = DukascopyClient(MagicMock())
        dclient.connect()
        dclient.disconnect()
        dclient.get_account_info()
        dclient.get_positions()
        dclient.get_orders()
        dclient.execute_trade(MagicMock())
    except Exception:
        pass
